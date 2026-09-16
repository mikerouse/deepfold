from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditEvent


def write_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    event_type: str,
    actor: str,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=str(entity_id),
        event_type=event_type,
        actor=actor,
        payload=payload or {},
    )
    db.add(event)
    return event
