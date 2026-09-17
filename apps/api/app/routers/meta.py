from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db import engine, get_db
from app.models import AuditEvent, Draft, PublishTarget
from app.schemas import AuditEventOut, HealthOut, PipelineOut, SettingsOut, StageCount
from app.services.pipeline import STAGE_ORDER, stage_for_status, stage_payload

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthOut)
def health():
    dialect = engine.dialect.name
    return HealthOut(
        status="ok",
        product="Deepfold Approvals Desk",
        database=dialect,
        kill_switch=settings.kill_switch,
        approve_and_publish_enabled=settings.approve_and_publish_enabled,
    )


@router.get("/settings", response_model=SettingsOut)
def get_settings():
    return SettingsOut(
        approve_and_publish_enabled=settings.approve_and_publish_enabled,
        kill_switch=settings.kill_switch,
        wp_live=settings.wp_live,
        default_actor=settings.default_actor,
        publisher_name=settings.publisher_name,
        product="Deepfold",
    )


@router.get("/pipeline", response_model=PipelineOut)
def get_pipeline(outlet_id: UUID | None = None, db: Session = Depends(get_db)):
    counts = {stage: 0 for stage in STAGE_ORDER}
    query = db.query(Draft)
    if outlet_id:
        query = query.filter(
            Draft.targets.any((PublishTarget.outlet_id == outlet_id) & (PublishTarget.selected.is_(True)))
        )
    for status, in query.with_entities(Draft.status).all():
        stage = stage_for_status(status)
        if stage in counts:
            counts[stage] += 1
    return PipelineOut(stages=[StageCount(**row) for row in stage_payload(counts)])


@router.get("/audit", response_model=list[AuditEventOut])
def list_audit(limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit).all()
