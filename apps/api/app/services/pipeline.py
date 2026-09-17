from __future__ import annotations

from app.enums import DecisionAction, DraftStatus, PipelineStage

STAGE_ORDER = [
    PipelineStage.pitch.value,
    PipelineStage.drafting.value,
    PipelineStage.checking.value,
    PipelineStage.publication.value,
    PipelineStage.social.value,
]

STAGE_LABELS = {
    PipelineStage.pitch.value: "Pitch",
    PipelineStage.drafting.value: "Drafting",
    PipelineStage.checking.value: "Checking",
    PipelineStage.publication.value: "Publication",
    PipelineStage.social.value: "Social",
}

STAGE_HINTS = {
    PipelineStage.pitch.value: "Abstract",
    PipelineStage.drafting.value: "Produce",
    PipelineStage.checking.value: "Review",
    PipelineStage.publication.value: "CMS draft",
    PipelineStage.social.value: "Stubs",
}

STAGE_EMPTY = {
    PipelineStage.pitch.value: "No pitches on the spike. Abstracts land here before anyone commissions a draft.",
    PipelineStage.drafting.value: "Nothing in drafting. Press Go on a pitch to commission the article, image plate, tags and outlets.",
    PipelineStage.checking.value: "Nothing to check. Drafts arrive here when the desk marks them ready.",
    PipelineStage.publication.value: "No CMS drafts yet. Approve from Checking to file WordPress drafts — never live by default.",
    PipelineStage.social.value: "No social stubs to review. They appear after a CMS draft is filed.",
}

# Statuses that live on each visible pipeline stage (archived no-go / reject are omitted).
STAGE_STATUSES: dict[str, set[str]] = {
    PipelineStage.pitch.value: {DraftStatus.pitch.value},
    PipelineStage.drafting.value: {DraftStatus.drafting.value},
    PipelineStage.checking.value: {
        DraftStatus.checking.value,
        DraftStatus.changes_requested.value,
        DraftStatus.held.value,
        DraftStatus.awaiting_review.value,
    },
    PipelineStage.publication.value: {DraftStatus.approved_cms_draft.value},
    PipelineStage.social.value: {DraftStatus.social.value, DraftStatus.published.value},
}

ARCHIVED_STATUSES = {DraftStatus.no_go.value, DraftStatus.rejected.value}

ACTIONS_BY_STAGE: dict[str, set[str]] = {
    PipelineStage.pitch.value: {
        DecisionAction.go.value,
        DecisionAction.no_go.value,
        DecisionAction.leave.value,
        DecisionAction.unleave.value,
        DecisionAction.outlet_override.value,
    },
    PipelineStage.drafting.value: {
        DecisionAction.send_to_checking.value,
        DecisionAction.return_to_pitch.value,
        DecisionAction.tweak.value,
        DecisionAction.outlet_override.value,
        DecisionAction.request_rewrite.value,
        DecisionAction.queue_featured_image.value,
    },
    PipelineStage.checking.value: {
        DecisionAction.approve_create_cms_drafts.value,
        DecisionAction.approve_publish.value,
        DecisionAction.request_changes.value,
        DecisionAction.reject.value,
        DecisionAction.hold.value,
        DecisionAction.tweak.value,
        DecisionAction.outlet_override.value,
        DecisionAction.return_to_pitch.value,
        DecisionAction.request_rewrite.value,
        DecisionAction.queue_featured_image.value,
    },
    PipelineStage.publication.value: {
        DecisionAction.advance_to_social.value,
        DecisionAction.approve_publish.value,
        DecisionAction.outlet_override.value,
        DecisionAction.tweak.value,
    },
    PipelineStage.social.value: {
        DecisionAction.social_edit.value,
        DecisionAction.social_approve.value,
        DecisionAction.social_hold.value,
        DecisionAction.approve_publish.value,
    },
}

# Seed rows that have never been touched still carry the v0 name.
LEGACY_CHECKING = DraftStatus.awaiting_review.value

SEED_STAGE_BY_SLUG = {
    "midlands-councils-40m-social-care": DraftStatus.pitch.value,
    "nuneaton-camphill-burglary-appeal": DraftStatus.drafting.value,
    "cabinet-member-housebuilder-meeting": DraftStatus.checking.value,
    "a5-hinckley-night-closures": DraftStatus.checking.value,
}


def stage_for_status(status: str) -> str | None:
    if status == LEGACY_CHECKING:
        return PipelineStage.checking.value
    for stage, statuses in STAGE_STATUSES.items():
        if status in statuses:
            return stage
    return None


def statuses_for_stage(stage: str) -> set[str]:
    return set(STAGE_STATUSES.get(stage, set()))


def action_allowed(stage: str | None, action: str) -> bool:
    if not stage:
        return False
    return action in ACTIONS_BY_STAGE.get(stage, set())


def next_status(action: str, current: str) -> str:
    mapping = {
        DecisionAction.go.value: DraftStatus.drafting.value,
        DecisionAction.no_go.value: DraftStatus.no_go.value,
        DecisionAction.return_to_pitch.value: DraftStatus.pitch.value,
        DecisionAction.send_to_checking.value: DraftStatus.checking.value,
        DecisionAction.advance_to_social.value: DraftStatus.social.value,
        DecisionAction.approve_create_cms_drafts.value: DraftStatus.approved_cms_draft.value,
        DecisionAction.approve_publish.value: DraftStatus.published.value,
        DecisionAction.request_changes.value: DraftStatus.changes_requested.value,
        DecisionAction.reject.value: DraftStatus.rejected.value,
        DecisionAction.hold.value: DraftStatus.held.value,
    }
    return mapping.get(action, current)


def commissioned_spine(headline: str, standfirst: str) -> str:
    abstract = standfirst.strip() or "Commissioned from the pitch abstract."
    return (
        f"{headline.strip()}\n\n{abstract}\n\n"
        "The desk has commissioned this draft. Spine, image plate, tags and outlet grafs "
        "are now in production for Checking."
    )


def stage_payload(counts: dict[str, int]) -> list[dict[str, str | int]]:
    rows = []
    for stage_id in STAGE_ORDER:
        rows.append(
            {
                "id": stage_id,
                "label": STAGE_LABELS[stage_id],
                "hint": STAGE_HINTS[stage_id],
                "count": counts.get(stage_id, 0),
                "empty": STAGE_EMPTY[stage_id],
            }
        )
    return rows
