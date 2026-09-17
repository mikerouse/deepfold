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
    county: str = ""
    region: str
    cms_kind: str
    cms_base_url: str
    default_selected: bool
    active: bool
    localisation_brief: str

    model_config = {"from_attributes": True}


class PackageOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    region: str
    county: str
    description: str
    outlets: list[OutletOut]

    model_config = {"from_attributes": True}


class OutletFacetsOut(BaseModel):
    regions: list[str]
    counties: list[str]


class OutletSuggestOut(BaseModel):
    outlets: list[OutletOut]
    packages: list[PackageOut]


class MediaAssetOut(BaseModel):
    id: uuid.UUID
    role: str
    caption: str
    alt_text: str
    credit: str
    policy_tag: str
    documentary_incident: bool
    placeholder_label: str
    url: str = ""
    prompt_version: str = ""

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


class PlatformChip(BaseModel):
    kind: str
    label: str
    outlet_id: uuid.UUID | None = None
    platform: str | None = None


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
    platforms: list[PlatformChip] = Field(default_factory=list)
    user_need: str | None = None
    selected_outlet_ids: list[uuid.UUID] = Field(default_factory=list)
    image_label: str | None = None
    draft_ready: bool = True
    worker_status: str | None = None
    worker_labels: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfidenceOut(BaseModel):
    score: float
    auto_draft_eligible: bool
    auto_publish_eligible: bool
    blocked_reasons: list[str]
    notes: list[str]


class JobOut(BaseModel):
    id: uuid.UUID
    draft_id: uuid.UUID
    kind: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any]
    worker: str | None
    error: str | None
    claimed_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobClaimIn(BaseModel):
    worker: str = "grok-bot"


class JobCompleteIn(BaseModel):
    worker: str = "grok-bot"
    error: str | None = None
    headline: str | None = None
    standfirst: str | None = None
    spine_body: str | None = None
    tags: list[str] | None = None
    placeholder_label: str | None = None
    caption: str | None = None
    alt_text: str | None = None
    credit: str | None = None
    url: str | None = None
    image_url: str | None = None
    prompt_version: str | None = None
    local_grafs: dict[str, str] | None = None
    social: list[dict[str, Any]] | None = None
    result: dict[str, Any] | None = None


class DraftVersionOut(BaseModel):
    version_number: int
    headline: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DraftDetail(DraftListItem):
    byline: str
    source_links: list[Any]
    geography: dict[str, Any] = Field(default_factory=dict)
    spine_body: str
    media: list[MediaAssetOut]
    social_posts: list[SocialPostOut]
    targets: list[PublishTargetOut]
    decisions: list[DecisionOut]
    jobs: list[JobOut] = Field(default_factory=list)
    versions: list[DraftVersionOut] = Field(default_factory=list)
    confidence: ConfidenceOut
    flags: dict[str, Any]
    is_pitch: bool = False
    generating: bool = False


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
    publisher_name: str = "Newsworld"
    product: str = "Deepfold"
    demo_instant_fulfill: bool = False
    demo_grok_worker: bool = False


class DemoTickOut(BaseModel):
    ok: bool
    simulating: str = "Grok Bot (demo worker, not an LLM call)"
    job: JobOut | None = None


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
