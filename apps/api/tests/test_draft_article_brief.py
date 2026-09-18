"""draft_article house-style briefs, job payload, and outlet routing."""

from pathlib import Path
from types import SimpleNamespace

CARE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BURGLARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
REDDITCH_ID = "55555555-5555-4555-8555-555555555555"

CP_BRIEF = Path(__file__).resolve().parents[1] / "app" / "prompts" / "draft_article_conservative_post_v1.md"
LOCAL_BRIEF = Path(__file__).resolve().parents[1] / "app" / "prompts" / "draft_article_local_v1.md"


def test_cp_brief_file_is_the_standing_house_style():
    text = CP_BRIEF.read_text(encoding="utf-8")
    assert "draft_article_conservative_post_v1" in text
    assert "PRO-BRITAIN, NOT PRO-GOVERNMENT" in text
    assert "Claire" in text and "Sep 2026" in text
    assert "spine_body" in text
    assert "OPENAI" not in text and "XAI_API_KEY" not in text
    assert "Do not dilute" in text


def test_local_brief_file_is_craft_without_cp_politics():
    text = LOCAL_BRIEF.read_text(encoding="utf-8")
    assert "draft_article_local_v1" in text
    assert "Political CP line does NOT apply" in text
    assert "Redditch Standard" in text
    assert "PRO-BRITAIN, NOT PRO-GOVERNMENT" not in text
    assert "OPENAI" not in text and "XAI_API_KEY" not in text


def _outlet(**kwargs):
    defaults = {"name": "Nuneaton Desk", "slug": "nuneaton-desk", "region": "West Midlands"}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _draft(outlets, **kwargs):
    targets = [SimpleNamespace(selected=True, outlet=o) for o in outlets]
    values = {
        "headline": "Midlands councils told to find £40m as social care bill climbs",
        "slug": "midlands-councils-40m-social-care",
        "standfirst": "Working papers set a savings figure.",
        "spine_body": "",
        "geography": {"counties": ["Warwickshire"], "towns": ["Nuneaton"]},
        "categories": ["Local government"],
        "tags": ["warwickshire"],
        "source_links": [{"url": "https://example.invalid", "label": "Council"}],
        "verification_status": "verified",
        "targets": targets,
    }
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_routes_conservative_post_to_cp_brief():
    from app.prompts.draft_article import CP_VERSION, draft_article_payload

    payload = draft_article_payload(_draft([_outlet(name="Conservative Post", slug="conservative-post", region="National")]))
    assert payload["brief_version"] == CP_VERSION
    assert payload["brief_path"].endswith("draft_article_conservative_post_v1.md")
    assert payload["base_brief"].strip()
    assert "PRO-BRITAIN, NOT PRO-GOVERNMENT" in payload["base_brief"]
    assert payload["house_style_label"] == "Conservative Post v1"
    assert payload["abstract"] == payload["standfirst"]
    assert payload["primary_outlet"]["slug"] == "conservative-post"


def test_routes_mixed_selection_to_cp_when_national_is_selected():
    from app.prompts.draft_article import CP_VERSION, draft_article_payload

    payload = draft_article_payload(
        _draft(
            [
                _outlet(name="Nuneaton Desk", slug="nuneaton-desk", region="West Midlands"),
                _outlet(name="Conservative Post", slug="conservative-post", region="National"),
            ]
        )
    )
    assert payload["brief_version"] == CP_VERSION
    assert payload["primary_outlet"]["slug"] == "conservative-post"


def test_routes_locals_to_local_craft():
    from app.prompts.draft_article import LOCAL_VERSION, draft_article_payload

    for outlet in (
        _outlet(name="Redditch News", slug="redditch-news", region="West Midlands"),
        _outlet(name="Bromsgrove Standard", slug="bromsgrove-standard", region="West Midlands"),
        _outlet(name="Worcester Observer", slug="worcester-observer", region="West Midlands"),
        _outlet(name="Nuneaton Desk", slug="nuneaton-desk", region="West Midlands"),
    ):
        payload = draft_article_payload(_draft([outlet]))
        assert payload["brief_version"] == LOCAL_VERSION, outlet.slug
        assert "Political CP line does NOT apply" in payload["base_brief"]
        assert "PRO-BRITAIN, NOT PRO-GOVERNMENT" not in payload["base_brief"]
        assert payload["house_style_label"] == "Local craft v1"


def test_unknown_or_empty_selection_defaults_to_local_craft():
    from app.prompts.draft_article import LOCAL_VERSION, draft_article_payload

    empty = draft_article_payload(_draft([]))
    assert empty["brief_version"] == LOCAL_VERSION
    assert empty["primary_outlet"] is None
    assert empty["base_brief"].strip()

    patriotic = draft_article_payload(
        _draft([_outlet(name="Patriotic Britain", slug="patriotic-britain", region="National")])
    )
    from app.prompts.draft_article import CP_VERSION

    assert patriotic["brief_version"] == CP_VERSION


def test_go_draft_article_payload_includes_cp_brief(client):
    body = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"}).json()
    job = next(j for j in body["jobs"] if j["kind"] == "draft_article")
    payload = job["payload"]
    assert job["status"] == "queued"
    assert payload["brief_version"] == "draft_article_conservative_post_v1"
    assert payload["brief_path"] == "apps/api/app/prompts/draft_article_conservative_post_v1.md"
    assert payload["base_brief"].strip()
    assert "PRO-BRITAIN, NOT PRO-GOVERNMENT" in payload["base_brief"]
    assert payload["headline"]
    assert payload["slug"] == "midlands-councils-40m-social-care"
    assert payload["standfirst"]
    assert payload["abstract"] == payload["standfirst"]
    assert "Warwickshire" in payload["geography"]["counties"]
    assert payload["house_style_label"] == "Conservative Post v1"
    assert payload["primary_outlet"]["slug"] == "conservative-post"


def test_go_with_local_titles_only_uses_local_craft(client):
    client.post(
        f"/drafts/{CARE_ID}/decisions",
        json={"action": "outlet_override", "selected_outlet_ids": [REDDITCH_ID]},
    )
    body = client.post(f"/drafts/{CARE_ID}/decisions", json={"action": "go"}).json()
    job = next(j for j in body["jobs"] if j["kind"] == "draft_article")
    payload = job["payload"]
    assert payload["brief_version"] == "draft_article_local_v1"
    assert payload["base_brief"].strip()
    assert "Political CP line does NOT apply" in payload["base_brief"]
    assert payload["primary_outlet"]["slug"] == "redditch-news"
    assert payload["house_style_label"] == "Local craft v1"


def test_request_rewrite_embeds_local_brief_for_nuneaton_story(client):
    body = client.post(f"/drafts/{BURGLARY_ID}/decisions", json={"action": "request_rewrite"}).json()
    job = next(j for j in body["jobs"] if j["kind"] == "draft_article" and j["status"] == "queued")
    payload = job["payload"]
    assert payload["brief_version"] == "draft_article_local_v1"
    assert payload["base_brief"].strip()
    assert payload["spine"] or payload["spine_body"]
    assert "Camp Hill" in payload["geography"]["towns"] or "Nuneaton" in payload["geography"]["towns"]
    listed = client.get(f"/jobs?draft_id={BURGLARY_ID}&kind=draft_article").json()
    queued = next(row for row in listed if row["status"] == "queued")
    assert queued["payload"]["brief_version"] == "draft_article_local_v1"
    assert queued["payload"]["base_brief"]


def test_seeded_jobs_carry_routed_briefs(client):
    burglary = client.get(f"/drafts/{BURGLARY_ID}").json()
    article = next(j for j in burglary["jobs"] if j["kind"] == "draft_article")
    assert article["payload"]["brief_version"] == "draft_article_local_v1"
    assert article["payload"]["base_brief"].strip()

    legal = client.get("/drafts/cccccccc-cccc-4ccc-8ccc-cccccccccccc").json()
    cp_job = next(j for j in legal["jobs"] if j["kind"] == "draft_article")
    assert cp_job["payload"]["brief_version"] == "draft_article_conservative_post_v1"
    assert "PRO-BRITAIN, NOT PRO-GOVERNMENT" in cp_job["payload"]["base_brief"]
