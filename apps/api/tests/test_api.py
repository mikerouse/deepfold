CARE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BURGLARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
LEGAL_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["approve_and_publish_enabled"] is False


def test_list_drafts(client):
    response = client.get("/drafts")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 4
    assert {row["slug"] for row in rows} >= {
        "midlands-councils-40m-social-care",
        "nuneaton-camphill-burglary-appeal",
    }


def test_get_draft(client):
    response = client.get(f"/drafts/{CARE_ID}")
    assert response.status_code == 200
    body = response.json()
    assert "social care" in body["headline"].lower() or "£40m" in body["headline"]
    assert body["media"]
    assert body["social_posts"]
    assert body["targets"]
    assert body["confidence"]["score"] > 0


def test_reject_requires_reason(client):
    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "reject"})
    assert response.status_code == 400


def test_hold_and_audit(client):
    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "hold", "reason": "waiting on county papers"})
    assert response.status_code == 200
    assert response.json()["status"] == "held"
    audit = client.get("/audit").json()
    assert any(event["event_type"] == "hold" for event in audit)


def test_approve_publish_blocked_by_flag(client):
    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "approve_publish"})
    assert response.status_code == 403


def test_approve_cms_drafts_dry_run(client):
    draft = client.get(f"/drafts/{CARE_ID}").json()
    outlet_ids = [t["outlet"]["id"] for t in draft["targets"] if t["selected"]]
    response = client.post(
        f"/drafts/{CARE_ID}/decisions",
        json={"action": "approve_create_cms_drafts", "selected_outlet_ids": outlet_ids},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved_cms_draft"
    assert body["decisions"][0]["action"] == "approve_create_cms_drafts"
    assert body["decisions"][0]["diff"]["cms"]


def test_single_source_can_still_be_held_by_human(client):
    response = client.post(f"/drafts/{BURGLARY_ID}/decisions", json={"action": "hold"})
    assert response.status_code == 200
    assert response.json()["verification_status"] == "single_source"


def test_request_changes_persists_reason(client):
    response = client.post(
        f"/drafts/{LEGAL_ID}/decisions",
        json={"action": "request_changes", "reason": "Need monitoring officer on the record."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "changes_requested"
    assert "monitoring officer" in response.json()["decisions"][0]["reason"]
