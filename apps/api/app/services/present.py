from __future__ import annotations

from app.config import settings
from app.models import Draft
from app.schemas import (
    ConfidenceOut,
    DecisionOut,
    DraftDetail,
    DraftListItem,
    MediaAssetOut,
    PublishTargetOut,
    SocialPostOut,
)
from app.services.confidence import score_draft


def suggested_outlet_names(draft: Draft) -> list[str]:
    names = []
    for target in draft.targets:
        if target.selected and target.outlet:
            names.append(target.outlet.name)
    return names


def to_list_item(draft: Draft) -> DraftListItem:
    return DraftListItem(
        id=draft.id,
        headline=draft.headline,
        standfirst=draft.standfirst,
        slug=draft.slug,
        status=draft.status,
        verification_status=draft.verification_status,
        categories=draft.categories or [],
        tags=draft.tags or [],
        confidence_score=draft.confidence_score,
        auto_draft_eligible=draft.auto_draft_eligible,
        auto_publish_eligible=draft.auto_publish_eligible,
        suggested_outlet_names=suggested_outlet_names(draft),
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
    return DraftDetail(
        **item.model_dump(),
        byline=draft.byline,
        source_links=draft.source_links or [],
        spine_body=draft.spine_body,
        media=[MediaAssetOut.model_validate(m) for m in draft.media],
        social_posts=[SocialPostOut.model_validate(s) for s in draft.social_posts],
        targets=[PublishTargetOut.model_validate(t) for t in draft.targets],
        decisions=[DecisionOut.model_validate(d) for d in sorted(draft.decisions, key=lambda x: x.created_at, reverse=True)],
        confidence=ConfidenceOut(**confidence),
        flags={
            "kill_switch": settings.kill_switch,
            "approve_and_publish_enabled": settings.approve_and_publish_enabled,
            "wp_live": settings.wp_live,
        },
    )
