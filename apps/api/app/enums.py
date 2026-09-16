import enum


class DraftStatus(str, enum.Enum):
    awaiting_review = "awaiting_review"
    changes_requested = "changes_requested"
    held = "held"
    approved_cms_draft = "approved_cms_draft"
    published = "published"
    rejected = "rejected"


class VerificationStatus(str, enum.Enum):
    verified = "verified"
    single_source = "single_source"
    caution = "caution"
    defamation_sensitive = "defamation_sensitive"


class DecisionAction(str, enum.Enum):
    approve_as_is = "approve_as_is"
    tweak = "tweak"
    approve_create_cms_drafts = "approve_create_cms_drafts"
    approve_publish = "approve_publish"
    request_changes = "request_changes"
    reject = "reject"
    hold = "hold"
    outlet_override = "outlet_override"
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
