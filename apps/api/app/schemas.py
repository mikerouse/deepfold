from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceLink(BaseModel):
    url: str
    label: str
    note: str = ""


class OutletOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    town: str
    region: str
    cms_kind: str
    cms_base_url: str
    default_selected: bool
    active: bool
    localisation_brief: str

    model_config = {"from_attributes": True}


class MediaAssetOut(BaseModel):
    id: uuid.UUID
    role: str
    caption: str
    alt_text: str
    credit: str
    policy_tag: str
    documentary_incident: bool
    placeholder_label: str

    model_config = {"from_attributes": True}


class SocialPostOut(BaseModel):
    id: uuid.UUID
    platform: str
    body: str
    edited_body: str | None
    status: str

    model_config = {"from_attributes": True}


class PublishTargetOut(BaseModel):
    id: uuid.UUID
    outlet: OutletOut
    selected: bool
    local_headline: str
    local_graf: str
    cms_status: str
    remote_post_id: str | None
    last_error: str | None

    model_config = {"from_attributes": True}


class DecisionOut(BaseModel):
    id: uuid.UUID
    actor: str
    action: str
    reason: str | None
    diff: dict[str, Any]
    previous_status: str
    new_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DraftListItem(BaseModel):
    id: uuid.UUID
    headline: str
    standfirst: str
    slug: str
    status: str
    pipeline_stage: str | None
    parked: bool = False
    verification_status: str
    categories: list[Any]
    tags: list[Any]
    confidence_score: float
    auto_draft_eligible: bool
    auto_publish_eligible: bool
    suggested_outlet_names: list[str]
    image_label: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfidenceOut(BaseModel):
    score: float
    auto_draft_eligible: bool
    auto_publish_eligible: bool
    blocked_reasons: list[str]
    notes: list[str]


class DraftDetail(DraftListItem):
    byline: str
    source_links: list[Any]
    spine_body: str
    media: list[MediaAssetOut]
    social_posts: list[SocialPostOut]
    targets: list[PublishTargetOut]
    decisions: list[DecisionOut]
    confidence: ConfidenceOut
    flags: dict[str, Any]
    is_pitch: bool = False


class DecisionCreate(BaseModel):
    action: str
    actor: str | None = None
    reason: str | None = None
    headline: str | None = None
    spine_body: str | None = None
    standfirst: str | None = None
    selected_outlet_ids: list[uuid.UUID] | None = None
    local_grafs: dict[str, str] | None = None
    social_post_id: uuid.UUID | None = None
    social_copy: str | None = None


class StageCount(BaseModel):
    id: str
    label: str
    hint: str
    count: int
    empty: str


class PipelineOut(BaseModel):
    stages: list[StageCount]


class SettingsOut(BaseModel):
    approve_and_publish_enabled: bool
    kill_switch: bool
    wp_live: bool
    default_actor: str
    product: str = "Deepfold Approvals Desk"


class AuditEventOut(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: str
    event_type: str
    actor: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthOut(BaseModel):
    status: str
    product: str
    database: str
    kill_switch: bool
    approve_and_publish_enabled: bool
