"""Jobs + outlet search/packages for a multi-title publisher desk."""

CARE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BURGLARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
REDDITCH_ID = "55555555-5555-4555-8555-555555555555"


def test_settings_exposes_publisher_not_a_single_masthead(client):
    body = client.get("/settings").json()
    assert body["publisher_name"] == "Newsworld"
    assert body["product"] == "Deepfold"


def test_outlet_search_does_not_dump_the_registry(client):
    all_titles = client.get("/outlets?limit=50").json()
    assert len(all_titles) >= 12
    redditch = client.get("/outlets?q=Redditch").json()
    assert len(redditch) == 1
    assert redditch[0]["slug"] == "redditch-news"
    assert redditch[0]["county"] == "Worcestershire"
    worcs = client.get("/outlets?county=Worcestershire").json()
    assert {row["slug"] for row in worcs} == {
        "redditch-news",
        "bromsgrove-standard",
        "worcester-chronicle",
    }


def test_worcestershire_package(client):
    packages = client.get("/outlets/packages").json()
    assert len(packages) == 1
    package = packages[0]
    assert "Worcestershire" in package["name"]
    assert [o["slug"] for o in package["outlets"]] == [
        "redditch-news",
        "bromsgrove-standard",
        "worcester-chronicle",
    ]
    facets = client.get("/outlets/facets").json()
    assert "Worcestershire" in facets["counties"]
    assert "West Midlands" in facets["regions"]


def test_suggest_uses_pitch_geography(client):
    body = client.get(f"/outlets/suggest?draft_id={CARE_ID}").json()
    slugs = {row["slug"] for row in body["outlets"]}
    assert "hinckley-desk" in slugs or "warwickshire-times" in slugs
    assert "worcester-chronicle" not in slugs
    names = {row["name"] for row in body["packages"]}
    assert any("Worcestershire" in name for name in names)


def test_go_completes_seeded_draft_job(client):
    queued_before = client.get("/jobs?status=queued").json()
    assert queued_before == []
    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"})
    assert response.status_code == 200
    body = response.json()
    assert body["pipeline_stage"] == "drafting"
    assert body["draft_ready"] is True
    assert body["generating"] is False
    assert "£40" in body["spine_body"] or "social care" in body["spine_body"].lower()
    assert body["media"]
    assert body["tags"]
    kinds = {job["kind"]: job["status"] for job in body["jobs"]}
    assert kinds["draft_article"] == "completed"
    assert kinds["featured_image"] == "completed"
    assert kinds["localize_outlets"] == "completed"


def test_go_without_spine_queues_draft_job(client):
    from uuid import UUID

    from app.db import SessionLocal
    from app.models import Draft

    db = SessionLocal()
    try:
        draft = db.get(Draft, UUID(CARE_ID))
        draft.spine_body = ""
        db.commit()
    finally:
        db.close()

    response = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"})
    assert response.status_code == 200
    body = response.json()
    assert body["pipeline_stage"] == "drafting"
    assert body["draft_ready"] is False
    assert body["generating"] is True
    assert body["spine_body"] == ""
    jobs = client.get(f"/jobs?draft_id={CARE_ID}&kind=draft_article").json()
    assert jobs[0]["status"] == "queued"

    job_id = jobs[0]["id"]
    claimed = client.post(f"/jobs/{job_id}/claim", json={"worker": "grok-bot"})
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "claimed"
    twice = client.post(f"/jobs/{job_id}/claim", json={"worker": "grok-bot-2"})
    assert twice.status_code == 409

    done = client.post(
        f"/jobs/{job_id}/complete",
        json={"worker": "grok-bot", "spine_body": "Councils were told to find forty million pounds.\n\nSecond graf."},
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    draft = client.get(f"/drafts/{CARE_ID}").json()
    assert draft["draft_ready"] is True
    assert "forty million" in draft["spine_body"]


def test_add_title_creates_publish_target(client):
    client.post(f"/drafts/{BURGLARY_ID}/decisions", json={"action": "send_to_checking"})
    response = client.post(
        f"/drafts/{BURGLARY_ID}/decisions",
        json={"action": "outlet_override", "selected_outlet_ids": [
            "22222222-2222-4222-8222-222222222222",
            REDDITCH_ID,
        ]},
    )
    assert response.status_code == 200
    slugs = {t["outlet"]["slug"] for t in response.json()["targets"] if t["selected"]}
    assert slugs == {"nuneaton-desk", "redditch-news"}
    redditch = next(t for t in response.json()["targets"] if t["outlet"]["slug"] == "redditch-news")
    assert redditch["local_graf"]


def test_drafting_seed_already_has_a_body(client):
    body = client.get(f"/drafts/{BURGLARY_ID}").json()
    assert body["pipeline_stage"] == "drafting"
    assert body["draft_ready"] is True
    assert "Camp Hill" in body["spine_body"]
    assert body["media"]
    assert {job["kind"] for job in body["jobs"]} >= {"draft_article", "featured_image"}
