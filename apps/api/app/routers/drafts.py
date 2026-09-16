from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import get_db
from app.enums import (
    HARD_BLOCK_VERIFICATIONS,
    DecisionAction,
    DraftStatus,
    PublishTargetStatus,
    SocialStatus,
)
from app.models import Decision, Draft, DraftVersion, PublishTarget, SocialPost
from app.schemas import DecisionCreate, DraftDetail, DraftListItem
from app.services.audit import write_audit
from app.services.localisation import compose_variant, fallback_local_graf
from app.services.present import apply_confidence, to_detail, to_list_item
from app.services.wordpress import WordPressAdapter

router = APIRouter(prefix="/drafts", tags=["drafts"])

REASON_REQUIRED = {DecisionAction.request_changes.value, DecisionAction.reject.value}


def _load_draft(db: Session, draft_id: uuid.UUID) -> Draft:
    draft = (
        db.query(Draft)
        .options(
            selectinload(Draft.targets).selectinload(PublishTarget.outlet),
            selectinload(Draft.media),
            selectinload(Draft.social_posts),
            selectinload(Draft.decisions),
            selectinload(Draft.versions),
        )
        .filter(Draft.id == draft_id)
        .one_or_none()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


def _snapshot(draft: Draft) -> dict[str, Any]:
    return {
        "headline": draft.headline,
        "standfirst": draft.standfirst,
        "spine_body": draft.spine_body,
        "status": draft.status,
        "targets": [
            {
                "outlet_id": str(t.outlet_id),
                "selected": t.selected,
                "local_graf": t.local_graf,
                "local_headline": t.local_headline,
            }
            for t in draft.targets
        ],
        "social": [
            {
                "id": str(s.id),
                "platform": s.platform,
                "status": s.status,
                "body": s.edited_body or s.body,
            }
            for s in draft.social_posts
        ],
    }


def _next_status(action: str, current: str) -> str:
    mapping = {
        DecisionAction.approve_create_cms_drafts.value: DraftStatus.approved_cms_draft.value,
        DecisionAction.approve_publish.value: DraftStatus.published.value,
        DecisionAction.request_changes.value: DraftStatus.changes_requested.value,
        DecisionAction.reject.value: DraftStatus.rejected.value,
        DecisionAction.hold.value: DraftStatus.held.value,
    }
    return mapping.get(action, current)


def _apply_copy_edits(draft: Draft, body: DecisionCreate) -> dict[str, Any]:
    diff: dict[str, Any] = {}
    if body.headline is not None and body.headline != draft.headline:
        diff["headline"] = {"from": draft.headline, "to": body.headline}
        draft.headline = body.headline
    if body.standfirst is not None and body.standfirst != draft.standfirst:
        diff["standfirst"] = {"from": draft.standfirst, "to": body.standfirst}
        draft.standfirst = body.standfirst
    if body.spine_body is not None and body.spine_body != draft.spine_body:
        diff["spine_body"] = {"from": draft.spine_body, "to": body.spine_body}
        draft.spine_body = body.spine_body
    return diff


def _apply_outlet_selection(draft: Draft, body: DecisionCreate) -> dict[str, Any]:
    diff: dict[str, Any] = {}
    if body.selected_outlet_ids is None and not body.local_grafs:
        return diff
    selected = set(str(i) for i in (body.selected_outlet_ids or []))
    before = [str(t.outlet_id) for t in draft.targets if t.selected]
    for target in draft.targets:
        if body.selected_outlet_ids is not None:
            target.selected = str(target.outlet_id) in selected
        if body.local_grafs and str(target.outlet_id) in body.local_grafs:
            new_graf = body.local_grafs[str(target.outlet_id)]
            if new_graf != target.local_graf:
                diff.setdefault("local_grafs", {})[str(target.outlet_id)] = {
                    "from": target.local_graf,
                    "to": new_graf,
                }
                target.local_graf = new_graf
    after = [str(t.outlet_id) for t in draft.targets if t.selected]
    if body.selected_outlet_ids is not None and before != after:
        diff["selected_outlets"] = {"from": before, "to": after}
    return diff


def _push_to_cms(draft: Draft, *, publish: bool, actor: str) -> list[dict[str, Any]]:
    adapter = WordPressAdapter()
    results = []
    selected = [t for t in draft.targets if t.selected]
    if not selected:
        raise HTTPException(status_code=400, detail="Select at least one outlet before approving.")
    for target in selected:
        outlet = target.outlet
        graf = target.local_graf or fallback_local_graf(outlet, draft.headline)
        target.local_graf = graf
        content = compose_variant(draft.spine_body, graf, outlet)
        title = target.local_headline or draft.headline
        result = adapter.create_post(outlet, title=title, content=content, publish=publish)
        if result.ok:
            target.cms_status = (
                PublishTargetStatus.published.value if publish else PublishTargetStatus.cms_draft_created.value
            )
            target.remote_post_id = result.remote_post_id
            target.last_error = None
        else:
            target.cms_status = PublishTargetStatus.failed.value
            target.last_error = result.detail
        results.append(
            {
                "outlet": outlet.slug,
                "ok": result.ok,
                "dry_run": result.dry_run,
                "status": result.status,
                "remote_post_id": result.remote_post_id,
                "detail": result.detail,
                "actor": actor,
            }
        )
    return results


@router.get("", response_model=list[DraftListItem])
def list_drafts(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Draft).options(selectinload(Draft.targets).selectinload(PublishTarget.outlet))
    if status:
        query = query.filter(Draft.status == status)
    drafts = query.order_by(Draft.created_at.desc()).all()
    return [to_list_item(d) for d in drafts]


@router.get("/{draft_id}", response_model=DraftDetail)
def get_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)):
    draft = _load_draft(db, draft_id)
    detail = to_detail(draft)
    db.commit()
    return detail


@router.post("/{draft_id}/decisions", response_model=DraftDetail)
def record_decision(draft_id: uuid.UUID, body: DecisionCreate, db: Session = Depends(get_db)):
    draft = _load_draft(db, draft_id)
    try:
        action = DecisionAction(body.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown action: {body.action}") from exc

    if action.value in REASON_REQUIRED and not (body.reason and body.reason.strip()):
        raise HTTPException(status_code=400, detail="A reason is required for this action.")

    actor = body.actor or settings.default_actor
    previous = draft.status
    diff: dict[str, Any] = {}
    cms_results: list[dict[str, Any]] = []

    copy_diff = _apply_copy_edits(draft, body)
    outlet_diff = _apply_outlet_selection(draft, body)
    diff.update(copy_diff)
    diff.update(outlet_diff)

    effective_action = action
    if action in {DecisionAction.approve_create_cms_drafts, DecisionAction.approve_publish} and copy_diff:
        # Human tweaked the spine while approving — persist that as part of the learning loop.
        diff["tweaked_on_approve"] = True

    if action == DecisionAction.outlet_override:
        if not outlet_diff:
            diff["outlet_override"] = "selection confirmed"
        effective_action = DecisionAction.outlet_override

    if action in {DecisionAction.social_edit, DecisionAction.social_approve, DecisionAction.social_hold}:
        if not body.social_post_id:
            raise HTTPException(status_code=400, detail="social_post_id is required for social actions.")
        post = next((s for s in draft.social_posts if s.id == body.social_post_id), None)
        if not post:
            raise HTTPException(status_code=404, detail="Social post not found on this draft.")
        before = {"status": post.status, "body": post.edited_body or post.body}
        if action == DecisionAction.social_edit:
            if not body.social_copy:
                raise HTTPException(status_code=400, detail="social_copy is required when editing.")
            post.edited_body = body.social_copy
            post.status = SocialStatus.edited.value
        elif action == DecisionAction.social_approve:
            if body.social_copy:
                post.edited_body = body.social_copy
                post.status = SocialStatus.edited.value if body.social_copy != post.body else SocialStatus.approved.value
            else:
                post.status = SocialStatus.approved.value
        else:
            post.status = SocialStatus.held.value
        diff["social"] = {
            "id": str(post.id),
            "platform": post.platform,
            "from": before,
            "to": {"status": post.status, "body": post.edited_body or post.body},
        }

    if action == DecisionAction.approve_publish:
        if settings.kill_switch:
            raise HTTPException(status_code=403, detail="Kill switch is on — publishing is blocked.")
        if not settings.approve_and_publish_enabled:
            raise HTTPException(
                status_code=403,
                detail="Approve & publish is feature-flagged off. Use Approve & create CMS drafts.",
            )
        if draft.verification_status in HARD_BLOCK_VERIFICATIONS:
            raise HTTPException(
                status_code=403,
                detail="Hard rule: never publish single-source, caution, or defamation-sensitive copy without a later workflow.",
            )
        cms_results = _push_to_cms(draft, publish=True, actor=actor)
        diff["cms"] = cms_results

    if action == DecisionAction.approve_create_cms_drafts:
        if settings.kill_switch:
            raise HTTPException(status_code=403, detail="Kill switch is on — CMS writes are blocked.")
        cms_results = _push_to_cms(draft, publish=False, actor=actor)
        diff["cms"] = cms_results

    if action == DecisionAction.tweak and not copy_diff:
        raise HTTPException(status_code=400, detail="tweak requires a headline, standfirst, or body change.")

    new_status = _next_status(effective_action.value, draft.status)
    draft.status = new_status

    version = DraftVersion(
        draft_id=draft.id,
        version_number=len(draft.versions) + 1,
        headline=draft.headline,
        spine_body=draft.spine_body,
        snapshot=_snapshot(draft),
        created_by=actor,
    )
    db.add(version)

    decision = Decision(
        draft_id=draft.id,
        actor=actor,
        action=effective_action.value,
        reason=body.reason,
        diff=diff,
        previous_status=previous,
        new_status=new_status,
    )
    db.add(decision)
    write_audit(
        db,
        entity_type="draft",
        entity_id=str(draft.id),
        event_type=effective_action.value,
        actor=actor,
        payload={"diff": diff, "previous_status": previous, "new_status": new_status, "reason": body.reason},
    )
    apply_confidence(draft)
    db.commit()
    return to_detail(_load_draft(db, draft.id))
