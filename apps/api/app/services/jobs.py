from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.enums import JobKind, JobStatus, MediaRole, SocialPlatform, SocialStatus
from app.models import Draft, DraftVersion, Job, MediaAsset, PublishTarget, SocialPost, utcnow
from app.prompts.draft_article import draft_article_payload
from app.prompts.featured_image import (
    BRIEF_VERSION,
    DEFAULT_CREDIT,
    featured_image_payload,
    plate_url_for,
)
from app.services.audit import write_audit
from app.services.localisation import fallback_local_graf

OPEN_STATUSES = {JobStatus.queued.value, JobStatus.claimed.value}
COMMISSION_KINDS = (
    JobKind.draft_article.value,
    JobKind.featured_image.value,
    JobKind.localize_outlets.value,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def pending_article_job(draft: Draft) -> Job | None:
    for job in draft.jobs or []:
        if job.kind == JobKind.draft_article.value and job.status in OPEN_STATUSES:
            return job
    return None


def article_job_completed(draft: Draft) -> bool:
    return any(
        job.kind == JobKind.draft_article.value and job.status == JobStatus.completed.value
        for job in (draft.jobs or [])
    )


def open_jobs(draft: Draft) -> list[Job]:
    return [job for job in (draft.jobs or []) if job.status in OPEN_STATUSES]


def draft_is_ready(draft: Draft) -> bool:
    if pending_article_job(draft):
        return False
    return bool((draft.spine_body or "").strip())


def _default_payload(draft: Draft, kind: str) -> dict[str, Any]:
    if kind == JobKind.featured_image.value:
        return featured_image_payload(draft)
    if kind == JobKind.draft_article.value:
        return draft_article_payload(draft)
    return {"headline": draft.headline, "slug": draft.slug}


def enqueue_job(db: Session, draft: Draft, kind: str, payload: dict[str, Any] | None = None) -> Job:
    for job in draft.jobs or []:
        if job.kind == kind and job.status in OPEN_STATUSES:
            return job
    job = Job(
        draft_id=draft.id,
        kind=kind,
        status=JobStatus.queued.value,
        payload=payload or _default_payload(draft, kind),
    )
    db.add(job)
    db.flush()
    if draft.jobs is not None:
        draft.jobs.append(job)
    write_audit(
        db,
        entity_type="job",
        entity_id=str(job.id),
        event_type="job_queued",
        actor="system",
        payload={"kind": kind, "draft_id": str(draft.id)},
    )
    return job


def enqueue_commission_jobs(db: Session, draft: Draft) -> list[Job]:
    jobs = [enqueue_job(db, draft, kind) for kind in COMMISSION_KINDS]
    return jobs


def enqueue_social_job(db: Session, draft: Draft) -> Job:
    return enqueue_job(db, draft, JobKind.social_stubs.value)


def cancel_open_jobs(db: Session, draft: Draft, *, reason: str, actor: str) -> int:
    n = 0
    for job in draft.jobs or []:
        if job.status in OPEN_STATUSES:
            job.status = JobStatus.cancelled.value
            job.error = reason
            job.updated_at = _now()
            n += 1
            write_audit(
                db,
                entity_type="job",
                entity_id=str(job.id),
                event_type="job_cancelled",
                actor=actor,
                payload={"kind": job.kind, "reason": reason},
            )
    return n


def claim_job(db: Session, job: Job, worker: str) -> Job:
    if job.status != JobStatus.queued.value:
        raise ValueError(f"Job is {job.status}, not queued.")
    job.status = JobStatus.claimed.value
    job.worker = worker
    job.claimed_at = utcnow()
    job.updated_at = _now()
    write_audit(
        db,
        entity_type="job",
        entity_id=str(job.id),
        event_type="job_claimed",
        actor=worker,
        payload={"kind": job.kind},
    )
    return job


def _write_version(db: Session, draft: Draft, actor: str) -> DraftVersion:
    version = DraftVersion(
        draft_id=draft.id,
        version_number=len(draft.versions) + 1,
        headline=draft.headline,
        spine_body=draft.spine_body,
        snapshot={"headline": draft.headline, "spine_body": draft.spine_body, "status": draft.status},
        created_by=actor,
    )
    db.add(version)
    return version


def _media_url(body: Any) -> str:
    return (getattr(body, "url", None) or getattr(body, "image_url", None) or "").strip()


def _apply_featured_image(db: Session, draft: Draft, body: Any) -> dict[str, Any]:
    url = _media_url(body)
    prompt_version = (getattr(body, "prompt_version", None) or "").strip() or BRIEF_VERSION
    placeholder = getattr(body, "placeholder_label", None)
    caption = getattr(body, "caption", None)
    alt_text = getattr(body, "alt_text", None)
    credit = getattr(body, "credit", None)
    has_fields = any([url, placeholder, caption, alt_text, credit, getattr(body, "prompt_version", None)])
    featured = next((m for m in (draft.media or []) if m.role == MediaRole.featured.value), None)
    if featured:
        if placeholder:
            featured.placeholder_label = placeholder
        if caption is not None:
            featured.caption = caption
        if alt_text is not None:
            featured.alt_text = alt_text
        if credit is not None:
            featured.credit = credit
        if url:
            featured.url = url
        featured.prompt_version = prompt_version
        featured.policy_tag = "saatchi_editorial"
        featured.documentary_incident = False
        return {"media": "updated", "url": featured.url, "prompt_version": featured.prompt_version}
    if not has_fields:
        return {}
    asset = MediaAsset(
        draft_id=draft.id,
        role=MediaRole.featured.value,
        placeholder_label=placeholder or "Editorial still",
        caption=caption or "",
        alt_text=alt_text or "",
        credit=credit or DEFAULT_CREDIT,
        policy_tag="saatchi_editorial",
        documentary_incident=False,
        url=url,
        prompt_version=prompt_version,
    )
    db.add(asset)
    db.flush()
    if draft.media is not None:
        draft.media.append(asset)
    return {"media": "created", "url": asset.url, "prompt_version": asset.prompt_version}


def apply_job_result(db: Session, draft: Draft, job: Job, body: Any, actor: str) -> dict[str, Any]:
    applied: dict[str, Any] = {}
    if job.kind == JobKind.draft_article.value:
        if getattr(body, "headline", None):
            draft.headline = body.headline
            applied["headline"] = body.headline
        if getattr(body, "standfirst", None):
            draft.standfirst = body.standfirst
            applied["standfirst"] = body.standfirst
        if getattr(body, "spine_body", None):
            draft.spine_body = body.spine_body
            applied["spine_body"] = True
        if getattr(body, "tags", None) is not None:
            draft.tags = body.tags
            applied["tags"] = body.tags
        _write_version(db, draft, actor)
    elif job.kind == JobKind.featured_image.value:
        applied.update(_apply_featured_image(db, draft, body))
    elif job.kind == JobKind.localize_outlets.value:
        grafs = getattr(body, "local_grafs", None) or {}
        for target in draft.targets:
            key = str(target.outlet_id)
            if key in grafs:
                target.local_graf = grafs[key]
                applied.setdefault("local_grafs", {})[key] = True
            elif target.selected and not (target.local_graf or "").strip():
                target.local_graf = fallback_local_graf(target.outlet, draft.headline)
    elif job.kind == JobKind.social_stubs.value:
        posts = getattr(body, "social", None) or []
        existing = {s.platform: s for s in draft.social_posts}
        for row in posts:
            platform = row.get("platform")
            copy = row.get("body") or ""
            if not platform or not copy:
                continue
            if platform in existing:
                existing[platform].body = copy
            else:
                db.add(
                    SocialPost(
                        draft_id=draft.id,
                        platform=platform if platform in {p.value for p in SocialPlatform} else SocialPlatform.x.value,
                        body=copy,
                        status=SocialStatus.pending.value,
                    )
                )
            applied.setdefault("social", []).append(platform)
    return applied


def complete_job(db: Session, job: Job, body: Any) -> Job:
    if job.status not in {JobStatus.queued.value, JobStatus.claimed.value}:
        raise ValueError(f"Job is {job.status}, not open.")
    actor = getattr(body, "worker", None) or job.worker or "grok-bot"
    if getattr(body, "error", None):
        job.status = JobStatus.failed.value
        job.error = body.error
        job.worker = actor
        job.completed_at = utcnow()
        job.updated_at = _now()
        write_audit(
            db,
            entity_type="job",
            entity_id=str(job.id),
            event_type="job_failed",
            actor=actor,
            payload={"kind": job.kind, "error": body.error},
        )
        return job

    draft = job.draft
    applied = apply_job_result(db, draft, job, body, actor)
    result = dict(getattr(body, "result", None) or {})
    result.update({"applied": applied, "kind": job.kind})
    job.status = JobStatus.completed.value
    job.worker = actor
    job.result = result
    job.error = None
    job.completed_at = utcnow()
    job.updated_at = _now()
    if job.status == JobStatus.completed.value and not job.claimed_at:
        job.claimed_at = job.completed_at
    write_audit(
        db,
        entity_type="job",
        entity_id=str(job.id),
        event_type="job_completed",
        actor=actor,
        payload={"kind": job.kind, "draft_id": str(draft.id), "applied": applied},
    )
    return job


def fulfill_seeded_commission(db: Session, draft: Draft, actor: str) -> list[Job]:
    """Demo path: if the pitch already has a spine/image/grafs, complete the Grok jobs in-process."""
    completed: list[Job] = []
    for job in list(draft.jobs or []):
        if job.status not in OPEN_STATUSES:
            continue
        if job.kind == JobKind.draft_article.value and (draft.spine_body or "").strip():
            job.status = JobStatus.completed.value
            job.worker = actor
            job.result = {"applied": {"spine_body": "seeded"}, "demo": True}
            job.claimed_at = utcnow()
            job.completed_at = job.claimed_at
            _write_version(db, draft, actor)
            completed.append(job)
        elif job.kind == JobKind.featured_image.value and draft.media:
            for asset in draft.media:
                if not (asset.url or "").strip():
                    asset.url = plate_url_for(draft.slug)
                if not (asset.prompt_version or "").strip():
                    asset.prompt_version = BRIEF_VERSION
                asset.documentary_incident = False
            job.status = JobStatus.completed.value
            job.worker = actor
            featured = next((m for m in draft.media if m.role == MediaRole.featured.value), draft.media[0])
            job.result = {
                "applied": {"media": "seeded", "url": featured.url, "prompt_version": featured.prompt_version},
                "demo": True,
            }
            job.claimed_at = utcnow()
            job.completed_at = job.claimed_at
            completed.append(job)
        elif job.kind == JobKind.localize_outlets.value and any((t.local_graf or "").strip() for t in draft.targets):
            job.status = JobStatus.completed.value
            job.worker = actor
            job.result = {"applied": {"local_grafs": "seeded"}, "demo": True}
            job.claimed_at = utcnow()
            job.completed_at = job.claimed_at
            completed.append(job)
        elif job.kind == JobKind.social_stubs.value and draft.social_posts:
            job.status = JobStatus.completed.value
            job.worker = actor
            job.result = {"applied": {"social": "seeded"}, "demo": True}
            job.claimed_at = utcnow()
            job.completed_at = job.claimed_at
            completed.append(job)
        if job in completed:
            write_audit(
                db,
                entity_type="job",
                entity_id=str(job.id),
                event_type="job_completed",
                actor=actor,
                payload={"kind": job.kind, "draft_id": str(draft.id), "demo": True},
            )
    return completed


def load_job(db: Session, job_id: uuid.UUID) -> Job | None:
    return (
        db.query(Job)
        .options(
            selectinload(Job.draft).selectinload(Draft.media),
            selectinload(Job.draft).selectinload(Draft.targets).selectinload(PublishTarget.outlet),
            selectinload(Job.draft).selectinload(Draft.social_posts),
            selectinload(Job.draft).selectinload(Draft.versions),
            selectinload(Job.draft).selectinload(Draft.jobs),
        )
        .filter(Job.id == job_id)
        .one_or_none()
    )
