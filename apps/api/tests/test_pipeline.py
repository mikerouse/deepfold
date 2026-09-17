CARE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BURGLARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ROADS_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"


def test_pipeline_counts(client):
    body = client.get("/pipeline").json()
    counts = {row["id"]: row["count"] for row in body["stages"]}
    assert [row["id"] for row in body["stages"]] == [
        "pitch",
        "drafting",
        "checking",
        "publication",
        "social",
    ]
    assert counts["pitch"] == 1
    assert counts["drafting"] == 1
    assert counts["checking"] == 2
    assert counts["publication"] == 0
    assert counts["social"] == 0


def test_list_by_stage(client):
    pitch = client.get("/drafts?stage=pitch").json()
    assert len(pitch) == 1
    assert pitch[0]["slug"] == "midlands-councils-40m-social-care"
    checking = client.get("/drafts?stage=checking").json()
    assert {row["slug"] for row in checking} == {
        "cabinet-member-housebuilder-meeting",
        "a5-hinckley-night-closures",
    }


def test_go_commissions_draft(client):
    hidden = client.get(f"/drafts/{CARE_ID}").json()
    assert hidden["spine_body"] == ""
    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "drafting"
    assert body["pipeline_stage"] == "drafting"
    assert body["is_pitch"] is False
    assert body["generating"] is True
    assert body["spine_body"] == ""
    kinds = {job["kind"]: job["status"] for job in body["jobs"]}
    assert kinds["draft_article"] == "queued"
    assert kinds["featured_image"] == "queued"
    counts = {row["id"]: row["count"] for row in client.get("/pipeline").json()["stages"]}
    assert counts["pitch"] == 0
    assert counts["drafting"] == 2


def test_leave_parks_and_unleave_undoes(client):
    left = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "leave"})
    assert left.status_code == 200
    body = left.json()
    assert body["status"] == "pitch"
    assert body["parked"] is True
    still_pitch = client.get("/drafts?stage=pitch").json()
    assert any(row["id"] == CARE_ID and row["parked"] for row in still_pitch)
    undone = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "unleave"})
    assert undone.json()["parked"] is False
    assert undone.json()["status"] == "pitch"


def test_no_go_requires_reason_and_archives(client):
    missing = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "no_go"})
    assert missing.status_code == 400
    killed = client.post(
        f"/drafts/{CARE_ID}/decisions",
        json={"action": "no_go", "reason": "Papers are not public yet — not a story this week."},
    )
    assert killed.status_code == 200
    assert killed.json()["status"] == "no_go"
    assert killed.json()["pipeline_stage"] is None
    listed = client.get("/drafts").json()
    assert CARE_ID not in {row["id"] for row in listed}
    pitch = client.get("/drafts?stage=pitch").json()
    assert pitch == []


def test_cannot_cms_from_pitch(client):
    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "approve_create_cms_drafts"})
    assert response.status_code == 400


def test_return_to_pitch_from_drafting(client):
    client.post(f"/drafts/{BURGLARY_ID}/decisions", json={"action": "return_to_pitch"})
    body = client.get(f"/drafts/{BURGLARY_ID}").json()
    assert body["status"] == "pitch"
    assert body["spine_body"] == ""


def test_go_does_not_wipe_spine(client):
    from uuid import UUID

    from app.db import SessionLocal
    from app.models import Draft

    client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go", "spine_body": ""})
    body = client.get(f"/drafts/{CARE_ID}").json()
    assert body["spine_body"] == ""
    db = SessionLocal()
    try:
        stored = db.get(Draft, UUID(CARE_ID))
        assert stored.spine_body.strip()
    finally:
        db.close()
