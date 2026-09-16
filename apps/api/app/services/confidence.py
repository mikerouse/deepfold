from __future__ import annotations

from app.enums import HARD_BLOCK_VERIFICATIONS, DecisionAction, VerificationStatus
from app.models import Decision, Draft


AUTO_DRAFT_THRESHOLD = 0.75
AUTO_PUBLISH_THRESHOLD = 0.9


def score_draft(
    draft: Draft,
    *,
    kill_switch: bool,
    approve_and_publish_enabled: bool,
    prior_decisions: list[Decision] | None = None,
) -> dict:
    """v0 heuristic stub. Later this can be replaced by a trained model.

    The learning loop already persists every human decision + diff, so a future
    scorer can train on approve-as-is vs tweak vs reject without a schema change.
    """
    notes: list[str] = []
    blocked: list[str] = []
    score = 0.48
    verification = draft.verification_status
    sources = draft.source_links or []
    decisions = prior_decisions if prior_decisions is not None else list(draft.decisions or [])

    if verification == VerificationStatus.verified.value:
        score += 0.22
        notes.append("Verification marked verified.")
    elif verification == VerificationStatus.single_source.value:
        score -= 0.18
        notes.append("Single-source copy is capped and can never auto-publish.")
    elif verification == VerificationStatus.caution.value:
        score -= 0.22
        notes.append("Caution flag: treat as human-only.")
    elif verification == VerificationStatus.defamation_sensitive.value:
        score -= 0.28
        notes.append("Defamation-sensitive: human legal read required.")

    if len(sources) >= 2:
        score += 0.1
        notes.append("Two or more source links.")
    elif len(sources) == 1:
        score -= 0.05
        notes.append("Only one source link on the draft.")

    approve_as_is = sum(1 for d in decisions if d.action == DecisionAction.approve_as_is.value)
    tweaks = sum(1 for d in decisions if d.action == DecisionAction.tweak.value)
    rejects = sum(
        1
        for d in decisions
        if d.action in {DecisionAction.reject.value, DecisionAction.request_changes.value}
    )
    overrides = sum(1 for d in decisions if d.action == DecisionAction.outlet_override.value)

    if approve_as_is:
        score += min(0.12, 0.04 * approve_as_is)
        notes.append("Prior approve-as-is decisions lift confidence.")
    if tweaks:
        score -= min(0.1, 0.03 * tweaks)
        notes.append("Journalist tweaks recorded — model should not assume the spine is clean.")
    if rejects:
        score -= min(0.2, 0.08 * rejects)
        notes.append("Reject / request-changes history on this draft.")
    if overrides:
        score -= 0.04
        notes.append("Outlet override recorded.")

    score = max(0.05, min(0.97, score))

    hard_block = verification in HARD_BLOCK_VERIFICATIONS
    if hard_block:
        blocked.append(f"hard-rule:{verification}")
        score = min(score, 0.34)

    if kill_switch:
        blocked.append("kill_switch")
    if not approve_and_publish_enabled:
        blocked.append("approve_and_publish_flag_off")

    auto_draft = (not hard_block) and (not kill_switch) and score >= AUTO_DRAFT_THRESHOLD
    auto_publish = (
        (not hard_block)
        and (not kill_switch)
        and approve_and_publish_enabled
        and verification == VerificationStatus.verified.value
        and score >= AUTO_PUBLISH_THRESHOLD
    )
    if hard_block:
        notes.append("Hard rule: never auto-draft or auto-publish this verification class.")
    if not auto_publish:
        notes.append("Auto-publish remains off unless score, verification, flag and kill switch all pass.")

    return {
        "score": round(score, 3),
        "auto_draft_eligible": auto_draft,
        "auto_publish_eligible": auto_publish,
        "blocked_reasons": blocked,
        "notes": notes,
    }
