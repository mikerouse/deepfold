"""Planning list: platforms, filters, pitch title targeting."""

CARE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BURGLARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ROADS_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
HINCKLEY_ID = "33333333-3333-4333-8333-333333333333"
REDDITCH_ID = "55555555-5555-4555-8555-555555555555"
WORCS_PACKAGE = "cccc1111-cccc-4111-8111-ccccccccc111"


def test_list_includes_web_and_social_platforms(client):
    rows = client.get("/drafts").json()
    assert len(rows) == 4
    care = next(row for row in rows if row["id"] == CARE_ID)
    kinds = [chip["kind"] for chip in care["platforms"]]
    labels = [chip["label"] for chip in care["platforms"]]
    assert kinds.count("web") >= 1
    assert kinds.count("social") >= 1
    assert "Conservative Post" in labels
    assert "X" in labels
    assert "Facebook" in labels
    assert care["user_need"] == "Update me"
    assert care["selected_outlet_ids"]


def test_user_need_is_a_quiet_stub(client):
    rows = {row["id"]: row["user_need"] for row in client.get("/drafts").json()}
    assert set(rows.values()) <= {"Update me", "Inform me", "Hold me to account", "Amuse me", None}
    assert rows[BURGLARY_ID] == "Inform me"
    assert rows[ROADS_ID] == "Inform me"


def test_filter_by_platform_type(client):
    web = client.get("/drafts?platform=web").json()
    social = client.get("/drafts?platform=social").json()
    assert len(web) == 4
    assert len(social) == 4
    bad = client.get("/drafts?platform=tiktok")
    assert bad.status_code == 400


def test_filter_by_county_uses_geography_and_titles(client):
    warwickshire = client.get("/drafts?county=Warwickshire").json()
    slugs = {row["slug"] for row in warwickshire}
    assert "midlands-councils-40m-social-care" in slugs
    assert "nuneaton-camphill-burglary-appeal" in slugs
    assert "a5-hinckley-night-closures" not in slugs
    leicestershire = client.get("/drafts?county=Leicestershire").json()
    leics = {row["slug"] for row in leicestershire}
    assert "a5-hinckley-night-closures" in leics
    assert "midlands-councils-40m-social-care" in leics


def test_filter_by_package_does_not_dump_unselected_titles(client):
    empty = client.get(f"/drafts?package_id={WORCS_PACKAGE}").json()
    assert empty == []
    client.post(
        f"/drafts/{BURGLARY_ID}/decisions",
        json={"action": "outlet_override", "selected_outlet_ids": [REDDITCH_ID]},
    )
    matched = client.get(f"/drafts?package_id={WORCS_PACKAGE}").json()
    assert {row["id"] for row in matched} == {BURGLARY_ID}


def test_filter_stage_and_county_together(client):
    rows = client.get("/drafts?stage=checking&county=Leicestershire").json()
    assert {row["slug"] for row in rows} == {"a5-hinckley-night-closures"}


def test_pitch_can_add_a_title_without_dumping_the_registry(client):
    draft = client.get(f"/drafts/{CARE_ID}").json()
    existing = [t["outlet"]["id"] for t in draft["targets"] if t["selected"]]
    response = client.post(
        f"/drafts/{CARE_ID}/decisions",
        json={"action": "outlet_override", "selected_outlet_ids": existing + [HINCKLEY_ID]},
    )
    assert response.status_code == 200
    assert response.json()["pipeline_stage"] == "pitch"
    names = [chip["label"] for chip in response.json()["platforms"] if chip["kind"] == "web"]
    assert "Hinckley Desk" in names
    listed = client.get("/drafts?stage=pitch").json()
    care = next(row for row in listed if row["id"] == CARE_ID)
    assert "Hinckley Desk" in [chip["label"] for chip in care["platforms"]]
