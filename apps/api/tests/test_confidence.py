from app.enums import VerificationStatus
from app.models import Draft
from app.services.confidence import score_draft


def _draft(**kwargs) -> Draft:
    values = {
        "headline": "Test",
        "spine_body": "Body",
        "verification_status": VerificationStatus.verified.value,
        "source_links": [{"url": "https://a.example", "label": "A"}, {"url": "https://b.example", "label": "B"}],
        "decisions": [],
    }
    values.update(kwargs)
    return Draft(**values)


def test_verified_multi_source_can_auto_draft_but_not_publish_when_flag_off():
    result = score_draft(_draft(), kill_switch=False, approve_and_publish_enabled=False)
    assert result["auto_draft_eligible"] is True
    assert result["auto_publish_eligible"] is False
    assert "approve_and_publish_flag_off" in result["blocked_reasons"]


def test_single_source_never_auto_publishes():
    result = score_draft(
        _draft(verification_status=VerificationStatus.single_source.value, source_links=[{"url": "https://a.example", "label": "A"}]),
        kill_switch=False,
        approve_and_publish_enabled=True,
    )
    assert result["auto_publish_eligible"] is False
    assert result["auto_draft_eligible"] is False
    assert any("single_source" in r for r in result["blocked_reasons"])


def test_caution_and_defamation_are_hard_blocked():
    for status in (VerificationStatus.caution.value, VerificationStatus.defamation_sensitive.value):
        result = score_draft(
            _draft(verification_status=status),
            kill_switch=False,
            approve_and_publish_enabled=True,
        )
        assert result["auto_publish_eligible"] is False
        assert result["auto_draft_eligible"] is False


def test_kill_switch_blocks_everything():
    result = score_draft(_draft(), kill_switch=True, approve_and_publish_enabled=True)
    assert result["auto_publish_eligible"] is False
    assert result["auto_draft_eligible"] is False
    assert "kill_switch" in result["blocked_reasons"]
