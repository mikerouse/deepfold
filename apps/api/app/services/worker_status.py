from __future__ import annotations

from app.enums import JobKind, JobStatus, PipelineStage
from app.models import Draft
from app.services.jobs import OPEN_STATUSES, draft_is_ready
from app.services.pipeline import stage_for_status

KIND_PRIORITY = (
    JobKind.draft_article.value,
    JobKind.featured_image.value,
    JobKind.localize_outlets.value,
    JobKind.social_stubs.value,
)

LABELS = {
    (JobKind.draft_article.value, JobStatus.queued.value): "Queued for drafting",
    (JobKind.draft_article.value, JobStatus.claimed.value): "Drafting…",
    (JobKind.featured_image.value, JobStatus.queued.value): "Queued for image",
    (JobKind.featured_image.value, JobStatus.claimed.value): "Generating image…",
    (JobKind.localize_outlets.value, JobStatus.queued.value): "Queued for titles",
    (JobKind.localize_outlets.value, JobStatus.claimed.value): "Localising…",
    (JobKind.social_stubs.value, JobStatus.queued.value): "Queued for social",
    (JobKind.social_stubs.value, JobStatus.claimed.value): "Writing social…",
}

READY_FOR_CHECK = "Ready for check"


def _open_by_kind(draft: Draft) -> dict[str, str]:
    found: dict[str, str] = {}
    for job in draft.jobs or []:
        if job.status not in OPEN_STATUSES:
            continue
        current = found.get(job.kind)
        if current == JobStatus.claimed.value:
            continue
        found[job.kind] = job.status
    return found


def worker_labels(draft: Draft, *, include_ready: bool = False) -> list[str]:
    """Human labels for open Grok Bot jobs, in newsroom priority order."""
    by_kind = _open_by_kind(draft)
    labels = [LABELS[kind, by_kind[kind]] for kind in KIND_PRIORITY if kind in by_kind]
    if include_ready and not labels:
        stage = stage_for_status(draft.status)
        if stage == PipelineStage.drafting.value and draft_is_ready(draft):
            labels.append(READY_FOR_CHECK)
    return labels


def worker_status(draft: Draft, *, include_ready: bool = False) -> str | None:
    labels = worker_labels(draft, include_ready=include_ready)
    return labels[0] if labels else None
