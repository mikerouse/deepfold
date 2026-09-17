from __future__ import annotations

from app.config import settings
from app.enums import PipelineStage, SocialPlatform
from app.models import Draft
from app.schemas import (
    ConfidenceOut,
    DecisionOut,
    DraftDetail,
    DraftListItem,
    DraftVersionOut,
    JobOut,
    MediaAssetOut,
    PlatformChip,
    PublishTargetOut,
    SocialPostOut,
)
from app.services.confidence import score_draft
from app.services.jobs import article_job_completed, draft_is_ready, pending_article_job
from app.services.pipeline import stage_for_status
from app.services.worker_status import worker_labels, worker_status

# Planning list stub — four intents, never the visual centre.
USER_NEED_INTENTS = ("Update me", "Inform me", "Hold me to account", "Amuse me")
CATEGORY_TO_NEED = {
    "local government": "Update me",
    "social care": "Update me",
    "crime": "Inform me",
    "transport": "Inform me",
    "planning": "Hold me to account",
    "accountability": "Hold me to account",
}
SOCIAL_LABELS = {
    SocialPlatform.x.value: "X",
    SocialPlatform.facebook.value: "Facebook",
}


def suggested_outlet_names(draft: Draft) -> list[str]:
    names = []
    for target in draft.targets:
        if target.selected and target.outlet:
            names.append(target.outlet.name)
    return names


def selected_outlet_ids(draft: Draft) -> list:
    return [target.outlet_id for target in draft.targets if target.selected]


def user_need_for(draft: Draft) -> str | None:
    for category in draft.categories or []:
        if not isinstance(category, str):
            continue
        mapped = CATEGORY_TO_NEED.get(category.strip().lower())
        if mapped in USER_NEED_INTENTS:
            return mapped
    return None


def platform_chips(draft: Draft) -> list[PlatformChip]:
    chips: list[PlatformChip] = []
    for target in draft.targets:
        if target.selected and target.outlet:
            chips.append(
                PlatformChip(kind="web", label=target.outlet.name, outlet_id=target.outlet.id)
            )
    for post in draft.social_posts or []:
        chips.append(
            PlatformChip(
                kind="social",
                label=SOCIAL_LABELS.get(post.platform, (post.platform or "").replace("_", " ").title()),
                platform=post.platform,
            )
        )
    return chips


def featured_image_label(draft: Draft) -> str | None:
    featured = next((m for m in (draft.media or []) if m.role == "featured"), None)
    if featured:
        return featured.placeholder_label
    if draft.media:
        return draft.media[0].placeholder_label
    return None


def waiting_on_first_draft(draft: Draft, is_pitch: bool) -> bool:
    if is_pitch:
        return False
    if article_job_completed(draft):
        return False
    return pending_article_job(draft) is not None or not (draft.spine_body or "").strip()


def to_list_item(draft: Draft) -> DraftListItem:
    stage = stage_for_status(draft.status)
    is_pitch = stage == PipelineStage.pitch.value
    labels = worker_labels(draft, include_ready=False)
    return DraftListItem(
        id=draft.id,
        headline=draft.headline,
        standfirst=draft.standfirst,
        slug=draft.slug,
        status=draft.status,
        pipeline_stage=stage,
        parked=bool(draft.parked),
        verification_status=draft.verification_status,
        categories=draft.categories or [],
        tags=draft.tags or [],
        confidence_score=draft.confidence_score,
        auto_draft_eligible=draft.auto_draft_eligible,
        auto_publish_eligible=draft.auto_publish_eligible,
        suggested_outlet_names=suggested_outlet_names(draft),
        platforms=platform_chips(draft),
        user_need=user_need_for(draft),
        selected_outlet_ids=selected_outlet_ids(draft),
        image_label=None if is_pitch else featured_image_label(draft),
        draft_ready=False if is_pitch else draft_is_ready(draft),
        worker_status=worker_status(draft, include_ready=False),
        worker_labels=labels,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def apply_confidence(draft: Draft) -> dict:
    result = score_draft(
        draft,
        kill_switch=settings.kill_switch,
        approve_and_publish_enabled=settings.approve_and_publish_enabled,
        prior_decisions=list(draft.decisions),
    )
    draft.confidence_score = result["score"]
    draft.auto_draft_eligible = result["auto_draft_eligible"]
    draft.auto_publish_eligible = result["auto_publish_eligible"]
    return result


def to_detail(draft: Draft) -> DraftDetail:
    confidence = apply_confidence(draft)
    item = to_list_item(draft)
    is_pitch = item.pipeline_stage == PipelineStage.pitch.value
    generating = waiting_on_first_draft(draft, is_pitch)
    labels = worker_labels(draft, include_ready=True)
    jobs = [JobOut.model_validate(j) for j in sorted(draft.jobs or [], key=lambda x: x.created_at, reverse=True)]
    versions = [
        DraftVersionOut.model_validate(v)
        for v in sorted(draft.versions or [], key=lambda x: x.version_number, reverse=True)
    ]
    item_data = item.model_dump()
    item_data["worker_status"] = labels[0] if labels else None
    item_data["worker_labels"] = labels
    return DraftDetail(
        **item_data,
        byline=draft.byline,
        source_links=draft.source_links or [],
        geography=draft.geography or {},
        spine_body="" if is_pitch or generating else draft.spine_body,
        media=[] if is_pitch else [MediaAssetOut.model_validate(m) for m in draft.media],
        social_posts=[] if is_pitch else [SocialPostOut.model_validate(s) for s in draft.social_posts],
        targets=[PublishTargetOut.model_validate(t) for t in draft.targets],
        decisions=[DecisionOut.model_validate(d) for d in sorted(draft.decisions, key=lambda x: x.created_at, reverse=True)],
        jobs=[] if is_pitch else jobs,
        versions=[] if is_pitch else versions,
        confidence=ConfidenceOut(**confidence),
        flags={
            "kill_switch": settings.kill_switch,
            "approve_and_publish_enabled": settings.approve_and_publish_enabled,
            "wp_live": settings.wp_live,
            "demo_instant_fulfill": settings.demo_instant_fulfill,
            "demo_grok_worker": settings.demo_grok_worker,
        },
        is_pitch=is_pitch,
        generating=generating,
    )
