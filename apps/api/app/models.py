from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Outlet(Base):
    __tablename__ = "outlets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    town: Mapped[str] = mapped_column(String(128), default="")
    region: Mapped[str] = mapped_column(String(128), default="")
    cms_kind: Mapped[str] = mapped_column(String(32), default="wordpress")
    cms_base_url: Mapped[str] = mapped_column(String(512), default="")
    default_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    localisation_brief: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    targets: Mapped[list[PublishTarget]] = relationship(back_populates="outlet")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    headline: Mapped[str] = mapped_column(String(500))
    standfirst: Mapped[str] = mapped_column(Text, default="")
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    byline: Mapped[str] = mapped_column(String(255), default="Deepfold AI draft")
    status: Mapped[str] = mapped_column(String(64), default="pitch", index=True)
    parked: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String(64), default="verified", index=True)
    categories: Mapped[list[Any]] = mapped_column(JSON, default=list)
    tags: Mapped[list[Any]] = mapped_column(JSON, default=list)
    source_links: Mapped[list[Any]] = mapped_column(JSON, default=list)
    spine_body: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    auto_draft_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_publish_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    versions: Mapped[list[DraftVersion]] = relationship(back_populates="draft", cascade="all, delete-orphan")
    targets: Mapped[list[PublishTarget]] = relationship(back_populates="draft", cascade="all, delete-orphan")
    decisions: Mapped[list[Decision]] = relationship(back_populates="draft", cascade="all, delete-orphan")
    media: Mapped[list[MediaAsset]] = relationship(back_populates="draft", cascade="all, delete-orphan")
    social_posts: Mapped[list[SocialPost]] = relationship(back_populates="draft", cascade="all, delete-orphan")


class DraftVersion(Base):
    __tablename__ = "draft_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drafts.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    headline: Mapped[str] = mapped_column(String(500))
    spine_body: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped[Draft] = relationship(back_populates="versions")


class PublishTarget(Base):
    __tablename__ = "publish_targets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drafts.id"), index=True)
    outlet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outlets.id"), index=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=True)
    local_headline: Mapped[str] = mapped_column(String(500), default="")
    local_graf: Mapped[str] = mapped_column(Text, default="")
    cms_status: Mapped[str] = mapped_column(String(64), default="pending")
    remote_post_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped[Draft] = relationship(back_populates="targets")
    outlet: Mapped[Outlet] = relationship(back_populates="targets")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drafts.id"), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    previous_status: Mapped[str] = mapped_column(String(64))
    new_status: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped[Draft] = relationship(back_populates="decisions")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drafts.id"), index=True)
    role: Mapped[str] = mapped_column(String(32), default="featured")
    caption: Mapped[str] = mapped_column(Text, default="")
    alt_text: Mapped[str] = mapped_column(Text, default="")
    credit: Mapped[str] = mapped_column(String(255), default="")
    policy_tag: Mapped[str] = mapped_column(String(64), default="saatchi_editorial")
    documentary_incident: Mapped[bool] = mapped_column(Boolean, default=False)
    placeholder_label: Mapped[str] = mapped_column(String(255), default="Editorial still")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped[Draft] = relationship(back_populates="media")


class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drafts.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(Text)
    edited_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped[Draft] = relationship(back_populates="social_posts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
