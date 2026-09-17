"""Featured-image brief, job payload, and MediaAsset complete path."""

from pathlib import Path

CARE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

BRIEF = Path(__file__).resolve().parents[1] / "app" / "prompts" / "featured_image_v1.md"


def test_brief_file_is_the_standing_recipe():
    text = BRIEF.read_text(encoding="utf-8")
    assert "featured_image_v1" in text
    assert "Saatchi rather than AI" in text
    assert "Story-specific scene:" in text
    assert "documentary" in text.lower()
    assert "prompt_version" in text
    assert "OPENAI" not in text and "XAI_API_KEY" not in text


def test_go_featured_image_payload_is_fully_specified(client):
    body = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"}).json()
    job = next(j for j in body["jobs"] if j["kind"] == "featured_image")
    payload = job["payload"]
    assert job["status"] == "completed"
    assert payload["brief_version"] == "featured_image_v1"
    assert payload["documentary_safe"] is True
    assert "civic" in payload["story_specific_scene"].lower() or "warwickshire" in payload["story_specific_scene"].lower()
    assert "Nuneaton" in payload["geography"]["towns"]
    assert "Saatchi rather than AI" in payload["base_brief"]
    assert "Story-specific scene:" in payload["base_brief"]
    featured = next(m for m in body["media"] if m["role"] == "featured")
    assert featured["url"] == "/plates/civic-dusk.svg"
    assert featured["prompt_version"] == "featured_image_v1"
    assert featured["documentary_incident"] is False
    assert "AI-generated" in featured["caption"] or "editorial" in featured["caption"].lower()


def test_featured_image_complete_creates_media_asset(client):
    from uuid import UUID

    from app.db import SessionLocal
    from app.models import Draft, MediaAsset

    db = SessionLocal()
    try:
        draft = db.get(Draft, UUID(CARE_ID))
        draft.spine_body = ""
        for asset in list(draft.media):
            db.delete(asset)
        db.commit()
    finally:
        db.close()

    go = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"})
    assert go.status_code == 200
    jobs = client.get(f"/jobs?draft_id={CARE_ID}&kind=featured_image").json()
    assert jobs[0]["status"] == "queued"
    payload = jobs[0]["payload"]
    assert payload["brief_version"] == "featured_image_v1"
    assert payload["documentary_safe"] is True
    assert payload["base_brief"]
    assert payload["story_specific_scene"]

    done = client.post(
        f"/jobs/{jobs[0]['id']}/complete",
        json={
            "worker": "grok-bot",
            "url": None,
            "image_url": "https://media.example.invalid/plates/civic.jpg",
            "alt_text": "Lit stone civic building at dusk, generic local-government illustration.",
            "caption": "Generic editorial plate; AI-generated illustration, not a photograph of a named meeting.",
            "prompt_version": "featured_image_v1",
            "placeholder_label": "County civic building — dusk exterior",
            "credit": "Desk stock / editorial illustration",
        },
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    assert done.json()["result"]["applied"]["media"] == "created"
    assert done.json()["result"]["applied"]["url"].endswith("civic.jpg")

    detail = client.get(f"/drafts/{CARE_ID}").json()
    featured = next(m for m in detail["media"] if m["role"] == "featured")
    assert featured["url"] == "https://media.example.invalid/plates/civic.jpg"
    assert featured["prompt_version"] == "featured_image_v1"
    assert featured["alt_text"].startswith("Lit stone")
    assert "AI-generated" in featured["caption"]
    assert featured["documentary_incident"] is False

    db = SessionLocal()
    try:
        rows = db.query(MediaAsset).filter(MediaAsset.draft_id == UUID(CARE_ID)).all()
        assert len(rows) == 1
        assert rows[0].url.endswith("civic.jpg")
    finally:
        db.close()


def test_story_specific_scene_is_documentary_safe():
    from app.prompts.featured_image import story_specific_scene

    crime = story_specific_scene(
        headline="Police appeal after burglary on Nuneaton estate — single statement only",
        standfirst="A rear door forced, jewellery taken.",
        spine="Warwickshire Police have appealed after a burglary.",
        geography={"counties": ["Warwickshire"], "towns": ["Nuneaton", "Camp Hill"]},
        categories=["Crime", "Nuneaton"],
    )
    low = crime.lower()
    assert "no incident" in low
    assert "jewellery" not in low
    assert "cctv" not in low
    assert "burgled house" not in low
    assert "1–3" not in crime
    assert crime.count(".") >= 2

    civic = story_specific_scene(
        headline="Midlands councils told to find £40m as social care bill climbs",
        standfirst="Working papers set a savings figure across Warwickshire authorities.",
        geography={"counties": ["Warwickshire"], "towns": ["Nuneaton"]},
        categories=["Local government", "Social care"],
    )
    assert "civic" in civic.lower()
    assert "named meeting" in civic.lower() or "not a named" in civic.lower()


def test_checking_seed_plate_has_url(client):
    roads = client.get("/drafts/dddddddd-dddd-4ddd-8ddd-dddddddddddd").json()
    featured = roads["media"][0]
    assert featured["url"] == "/plates/carriageway-dusk.svg"
    assert featured["prompt_version"] == "featured_image_v1"
    assert featured["caption"]
