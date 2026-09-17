import enum


class PipelineStage(str, enum.Enum):
    pitch = "pitch"
    drafting = "drafting"
    checking = "checking"
    publication = "publication"
    social = "social"


class DraftStatus(str, enum.Enum):
    pitch = "pitch"
    drafting = "drafting"
    checking = "checking"
    changes_requested = "changes_requested"
    held = "held"
    approved_cms_draft = "approved_cms_draft"
    social = "social"
    published = "published"
    no_go = "no_go"
    rejected = "rejected"
    # Legacy name kept so old rows/docs still parse until migrated.
    awaiting_review = "awaiting_review"


class VerificationStatus(str, enum.Enum):
    verified = "verified"
    single_source = "single_source"
    caution = "caution"
    defamation_sensitive = "defamation_sensitive"


class DecisionAction(str, enum.Enum):
    go = "go"
    no_go = "no_go"
    leave = "leave"
    unleave = "unleave"
    return_to_pitch = "return_to_pitch"
    send_to_checking = "send_to_checking"
    advance_to_social = "advance_to_social"
    approve_as_is = "approve_as_is"
    tweak = "tweak"
    approve_create_cms_drafts = "approve_create_cms_drafts"
    approve_publish = "approve_publish"
    request_changes = "request_changes"
    reject = "reject"
    hold = "hold"
    outlet_override = "outlet_override"
    request_rewrite = "request_rewrite"
    queue_featured_image = "queue_featured_image"
    social_edit = "social_edit"
    social_approve = "social_approve"
    social_hold = "social_hold"


class SocialPlatform(str, enum.Enum):
    x = "x"
    facebook = "facebook"


class SocialStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    edited = "edited"
    held = "held"


class MediaRole(str, enum.Enum):
    featured = "featured"
    inline = "inline"


class CmsKind(str, enum.Enum):
    wordpress = "wordpress"
    stub = "stub"


class PublishTargetStatus(str, enum.Enum):
    pending = "pending"
    cms_draft_created = "cms_draft_created"
    published = "published"
    blocked = "blocked"
    failed = "failed"


HARD_BLOCK_VERIFICATIONS = {
    VerificationStatus.single_source.value,
    VerificationStatus.caution.value,
    VerificationStatus.defamation_sensitive.value,
}


class JobKind(str, enum.Enum):
    draft_article = "draft_article"
    featured_image = "featured_image"
    localize_outlets = "localize_outlets"
    social_stubs = "social_stubs"


class JobStatus(str, enum.Enum):
    queued = "queued"
    claimed = "claimed"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
