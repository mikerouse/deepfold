"""Localhost stand-in for Grok Bot. Completes jobs with seed/stub copy. Not an LLM call."""

from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.enums import JobKind, JobStatus, MediaRole, SocialPlatform
from app.models import Draft, Job
from app.prompts.featured_image import BRIEF_VERSION, DEFAULT_CREDIT, plate_url_for, story_specific_scene
from app.schemas import JobCompleteIn, JobOut
from app.services.jobs import claim_job, complete_job, load_job
from app.services.localisation import fallback_local_graf
from app.services.pipeline import commissioned_spine

logger = logging.getLogger(__name__)

DEMO_WORKER = "demo-grok-bot"
DEMO_NOTE = "Simulating Grok Bot only — stub/seed content, not an LLM call."


def _featured_fields(draft: Draft, job: Job) -> dict[str, Any]:
    featured = next((m for m in (draft.media or []) if m.role == MediaRole.featured.value), None)
    payload = job.payload or {}
    scene = payload.get("story_specific_scene") or story_specific_scene(
        headline=draft.headline,
        standfirst=draft.standfirst or "",
        spine=draft.spine_body or "",
        geography=draft.geography or {},
        categories=draft.categories,
    )
    placeholder = (featured.placeholder_label if featured else None) or scene.split(".")[0][:120]
    return {
        "url": ((featured.url if featured else "") or plate_url_for(draft.slug)),
        "alt_text": (featured.alt_text if featured else "")
        or "Generic editorial still; not a photograph of a named incident.",
        "caption": (featured.caption if featured else "")
        or "Generic editorial still; AI-generated illustration, not a photograph of the event.",
        "prompt_version": (featured.prompt_version if featured else "") or BRIEF_VERSION,
        "placeholder_label": placeholder,
        "credit": (featured.credit if featured else "") or DEFAULT_CREDIT,
    }


def stub_complete_body(job: Job) -> JobCompleteIn:
    draft = job.draft
    if job.kind == JobKind.draft_article.value:
        spine = (draft.spine_body or "").strip() or commissioned_spine(draft.headline, draft.standfirst)
        return JobCompleteIn(
            worker=DEMO_WORKER,
            headline=draft.headline,
            standfirst=draft.standfirst,
            spine_body=spine,
            tags=list(draft.tags or []),
            result={"demo": True, "simulating": DEMO_NOTE},
        )
    if job.kind == JobKind.featured_image.value:
        fields = _featured_fields(draft, job)
        return JobCompleteIn(worker=DEMO_WORKER, result={"demo": True, "simulating": DEMO_NOTE}, **fields)
    if job.kind == JobKind.localize_outlets.value:
        grafs: dict[str, str] = {}
        for target in draft.targets:
            if not target.selected:
                continue
            grafs[str(target.outlet_id)] = (target.local_graf or "").strip() or fallback_local_graf(
                target.outlet, draft.headline
            )
        return JobCompleteIn(worker=DEMO_WORKER, local_grafs=grafs, result={"demo": True, "simulating": DEMO_NOTE})
    posts = [
        {"platform": post.platform, "body": post.edited_body or post.body}
        for post in (draft.social_posts or [])
        if (post.edited_body or post.body or "").strip()
    ]
    if not posts:
        lead = (draft.standfirst or draft.headline).strip()
        posts = [
            {"platform": SocialPlatform.x.value, "body": draft.headline[:180]},
            {"platform": SocialPlatform.facebook.value, "body": lead},
        ]
    return JobCompleteIn(worker=DEMO_WORKER, social=posts, result={"demo": True, "simulating": DEMO_NOTE})


def _next_queued_id(db: Session) -> Job | None:
    return (
        db.query(Job)
        .filter(Job.status == JobStatus.queued.value)
        .order_by(Job.created_at.asc())
        .first()
    )


def run_demo_tick(delay_seconds: float | None = None) -> JobOut | None:
    """Claim the oldest queued job as the demo worker, wait, then complete with stub copy."""
    delay = settings.demo_grok_worker_delay_seconds if delay_seconds is None else delay_seconds
    db = SessionLocal()
    job_id = None
    try:
        queued = _next_queued_id(db)
        if not queued:
            return None
        job = load_job(db, queued.id)
        if not job:
            return None
        claim_job(db, job, DEMO_WORKER)
        db.commit()
        job_id = job.id
    finally:
        db.close()

    if delay and delay > 0:
        time.sleep(delay)

    db = SessionLocal()
    try:
        job = load_job(db, job_id)
        if not job or job.status != JobStatus.claimed.value:
            return JobOut.model_validate(job) if job else None
        complete_job(db, job, stub_complete_body(job))
        db.commit()
        db.refresh(job)
        logger.info("Demo Grok worker completed %s (%s)", job.id, job.kind)
        return JobOut.model_validate(job)
    finally:
        db.close()
