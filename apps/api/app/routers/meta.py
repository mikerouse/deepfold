from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db import engine, get_db
from app.models import AuditEvent
from app.schemas import AuditEventOut, HealthOut, SettingsOut

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
    )


@router.get("/audit", response_model=list[AuditEventOut])
def list_audit(limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit).all()
