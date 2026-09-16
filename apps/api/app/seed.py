from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db import SessionLocal, init_db
from app.enums import MediaRole, SocialPlatform, SocialStatus, VerificationStatus
from app.models import Draft, MediaAsset, Outlet, PublishTarget, SocialPost
from app.services.audit import write_audit
from app.services.present import apply_confidence

OUTLET_SPECS = [
    {
        "id": uuid.UUID("11111111-1111-4111-8111-111111111111"),
        "name": "Conservative Post",
        "slug": "conservative-post",
        "town": "Westminster",
        "region": "National",
        "cms_kind": "wordpress",
        "cms_base_url": "https://www.conservativepost.co.uk",
        "default_selected": True,
        "localisation_brief": "National conservative frame; still name the towns. Avoid parliamentary jargon without a local consequence.",
    },
    {
        "id": uuid.UUID("22222222-2222-4222-8222-222222222222"),
        "name": "Nuneaton Desk",
        "slug": "nuneaton-desk",
        "town": "Nuneaton",
        "region": "Warwickshire",
        "cms_kind": "wordpress",
        "cms_base_url": "https://nuneaton.example.invalid",
        "default_selected": True,
        "localisation_brief": "Nuneaton & Bedworth: name wards, the Town Hall, and the A444.",
    },
    {
        "id": uuid.UUID("33333333-3333-4333-8333-333333333333"),
        "name": "Hinckley Desk",
        "slug": "hinckley-desk",
        "town": "Hinckley",
        "region": "Leicestershire",
        "cms_kind": "wordpress",
        "cms_base_url": "https://hinckley.example.invalid",
        "default_selected": False,
        "localisation_brief": "Hinckley & Bosworth: A5, borough council, market town traders.",
    },
    {
        "id": uuid.UUID("44444444-4444-4444-8444-444444444444"),
        "name": "Warwickshire Times",
        "slug": "warwickshire-times",
        "town": "Warwick",
        "region": "Warwickshire",
        "cms_kind": "wordpress",
        "cms_base_url": "https://warwickshire.example.invalid",
        "default_selected": False,
        "localisation_brief": "County-wide; Shire Hall and county cabinet, not a single borough.",
    },
]


def _body_care() -> str:
    return """Warwickshire’s district and borough leaders have been told to find tens of millions of pounds in savings as the adult social care bill continues to climb faster than council tax.

Papers circulated to section 151 officers set a working figure of £40 million across the county’s local authorities over the medium-term financial plan. Officials say the pressure is not a one-off “efficiency drive” but the compound effect of placements, hospital discharge, and a workforce that local government can no longer recruit at yesterday’s rates.

Conservative group leaders argue that the settlement from Whitehall still assumes growth in business rates and council tax that many Midlands towns simply do not have. Labour and Liberal Democrat groups on the same councils counter that reserves have already been used to postpone the choice.

None of the papers published this week name a specific library, leisure centre or care home for closure. That is the next round. What they do set is a timetable: draft budgets in December, public consultation in the new year, and statutory council tax meetings before March.

A county hall spokesman said the authority remained committed to protecting “the most vulnerable” and that no decisions had been taken. Opposition councillors called that a holding line until the private papers become public reports.
"""


def _body_burglary() -> str:
    return """Warwickshire Police have appealed for witnesses after a burglary on a Nuneaton housing estate in the early hours of Tuesday.

The force said a rear door was forced at a semi-detached house in the Camp Hill area and that jewellery and a tablet computer were taken. Neighbours reported hearing a van pull away shortly after 2am. No arrests have been announced.

The account published this morning rests on a single police statement. Officers have not yet released CCTV, a suspect description, or confirmation that the same method has been used on nearby streets.

Residents told a reporter at the scene that this was the third break-in they had heard of this month. Those claims have not been verified against crime records and must not be written as established fact.

Police asked anyone with doorbell footage from between 1.30am and 2.30am to come forward via 101, quoting the incident number in the statement.
"""


def _body_lobbying() -> str:
    return """Questions have been raised about a private meeting between a cabinet member with planning in their portfolio and a director of a Midlands housebuilder with a live outline application on the edge of town.

The meeting is not in the published forward plan. It appears only as a one-line diary entry released after an opposition councillor asked for hospitality and meeting records. The councillor alleges the discussion went to density and Section 106 contributions. The cabinet member’s office says it was a “courtesy catch-up” and that no decision was taken.

No document we have seen proves that planning policy was altered in that room. Treating the allegation as proven would be unsafe. What can be said, on the record, is that the meeting happened, the application is live, and the published transparency record was thin.

The housebuilder was invited to comment and had not replied when this draft was filed. The monitoring officer has been asked whether the meeting should have been logged as a related-party contact.

This copy must not name the alleged private remarks as fact. The journalist’s job on the desk is to decide whether the public-interest test is met for the diary discrepancy alone, or whether the piece still needs a second source.
"""


def _body_roads() -> str:
    return """National Highways is to close night-time lanes on a stretch of the A5 around Hinckley for a fortnight of resurfacing, starting Monday.

The works are booked between 8pm and 6am on weekdays. A signed diversion will send through-traffic via local distributor roads. Daytime running will remain two-way, with a 40mph limit through the site.

A Highways spokesman said the surface had reached the end of its life and that completing the job in a single block would reduce the number of repeat closures. County highways asked drivers not to rat-run through residential streets during the diversion.

Traders on the ring of streets nearest the junction say previous night works still left the morning peak “looking like a Saturday market with HGVs”. That is colour, not a traffic model.

The scheme is routine, fully sourced from the Highways notice and the county’s own diversion map, and is the sort of copy a future high-confidence pipeline could auto-draft — still not auto-publish until a journalist has looked at the diversion and the dates.
"""


def seed_if_empty() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Outlet).count() > 0:
            return
        _seed(db)
        db.commit()
    finally:
        db.close()


def _seed(db: Session) -> None:
    outlets: dict[str, Outlet] = {}
    for spec in OUTLET_SPECS:
        outlet = Outlet(**spec)
        db.add(outlet)
        outlets[spec["slug"]] = outlet
    db.flush()

    drafts = [
        {
            "id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            "headline": "Midlands councils told to find £40m as social care bill climbs",
            "standfirst": "Working papers set a savings figure across Warwickshire authorities — no closures named yet, but the December budget round will have to.",
            "slug": "midlands-councils-40m-social-care",
            "verification_status": VerificationStatus.verified.value,
            "categories": ["Local government", "Social care"],
            "tags": ["warwickshire", "budgets", "adult-social-care"],
            "source_links": [
                {
                    "url": "https://www.warwickshire.gov.uk/",
                    "label": "Warwickshire County Council",
                    "note": "Statutory home; papers themselves are not yet in the public reports pack.",
                },
                {
                    "url": "https://www.gov.uk/government/organisations/ministry-of-housing-communities-local-government",
                    "label": "MHCLG",
                    "note": "Settlement context.",
                },
            ],
            "spine_body": _body_care(),
            "outlets": {
                "conservative-post": "Nationally this is another Midlands shire being asked to absorb a care market Whitehall still prices as if every town had London’s tax base.",
                "nuneaton-desk": "In Nuneaton, members will be asked what a county-wide savings line means for the Borough’s own leisure and homelessness budgets — the Town Hall cannot wait for Shire Hall’s March meeting.",
                "hinckley-desk": "Hinckley & Bosworth members will want the figure translated into a borough implication before the consultation leaflets go out, particularly for older residents off the A5 corridor.",
                "warwickshire-times": "At Shire Hall the political fight is over whether the £40m is a planning assumption or a target already being baked into directorate envelopes.",
            },
            "default_selected": ["conservative-post", "nuneaton-desk"],
            "media": [
                {
                    "role": MediaRole.featured.value,
                    "placeholder_label": "County civic building — dusk exterior",
                    "caption": "Stock civic exterior for a budget story. Saatchi-style editorial still; not a photograph of any named meeting.",
                    "alt_text": "Lit stone civic building at dusk, used as a generic illustration of local government.",
                    "credit": "Desk stock / editorial illustration",
                    "policy_tag": "saatchi_editorial",
                    "documentary_incident": False,
                }
            ],
            "social": {
                "x": "Warwickshire councils have been told to find £40m as the adult social care bill climbs. No closures named yet — the December budget round is when the line items appear.",
                "facebook": "Working papers put a £40 million savings figure across Warwickshire authorities as social care costs keep rising. Nothing is named for closure yet. The public argument starts when those papers become budget reports.",
            },
        },
        {
            "id": uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            "headline": "Police appeal after burglary on Nuneaton estate — single statement only",
            "standfirst": "A rear door forced, jewellery taken, a van heard leaving. One police notice; neighbours’ “third this month” claims are unverified.",
            "slug": "nuneaton-camphill-burglary-appeal",
            "verification_status": VerificationStatus.single_source.value,
            "categories": ["Crime", "Nuneaton"],
            "tags": ["police", "camphill", "single-source"],
            "source_links": [
                {
                    "url": "https://www.warwickshire.police.uk/",
                    "label": "Warwickshire Police",
                    "note": "Sole on-the-record source in this draft.",
                }
            ],
            "spine_body": _body_burglary(),
            "outlets": {
                "nuneaton-desk": "Camp Hill will read this as a street-level story: which end of the estate, which van, and whether the “third this month” claim survives a check against recorded crime.",
                "conservative-post": "Carry only if the desk is satisfied the public-appeal element is new; do not inflate a single force statement into a crimewave.",
            },
            "default_selected": ["nuneaton-desk"],
            "media": [
                {
                    "role": MediaRole.featured.value,
                    "placeholder_label": "Generic suburban street — daylight",
                    "caption": "Generic suburban street stock. Not the burgled house, not the estate, not reconstructed CCTV. Documentary incident photography is forbidden here.",
                    "alt_text": "Unidentified residential street in daylight, used only as a non-incident illustration.",
                    "credit": "Desk stock / editorial illustration",
                    "policy_tag": "saatchi_editorial",
                    "documentary_incident": False,
                }
            ],
            "social": {
                "x": "HOLD until the desk decides the single-source police appeal is enough. Do not tweet neighbours’ unverified burglary tally.",
                "facebook": "Police have appealed for doorbell footage after a burglary in Nuneaton. Further detail is limited; we are not repeating unverified neighbour claims.",
            },
        },
        {
            "id": uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            "headline": "Diary gap around cabinet member’s meeting with housebuilder",
            "standfirst": "A live outline application, a thin transparency record, and an allegation we cannot treat as proved. Legal read required.",
            "slug": "cabinet-member-housebuilder-meeting",
            "verification_status": VerificationStatus.defamation_sensitive.value,
            "categories": ["Planning", "Accountability"],
            "tags": ["defamation", "planning", "transparency"],
            "source_links": [
                {
                    "url": "https://www.gov.uk/guidance/openness-and-transparency-on-personal-interests",
                    "label": "Openness guidance",
                    "note": "Context for what should have been logged.",
                },
                {
                    "url": "https://www.legislation.gov.uk/ukpga/2011/20/contents",
                    "label": "Localism Act 2011",
                    "note": "Interests regime — not evidence of a breach.",
                },
            ],
            "spine_body": _body_lobbying(),
            "outlets": {
                "conservative-post": "National frame is standards in public life, not a named smear. If we cannot evidence the alleged remarks, we do not print them.",
                "warwickshire-times": "County readers need the application named only if the planning reference is already public; do not identify a private individual beyond their public office without the lawyer.",
            },
            "default_selected": ["conservative-post"],
            "media": [
                {
                    "role": MediaRole.featured.value,
                    "placeholder_label": "Empty committee chamber — lights on",
                    "caption": "Empty chamber, editorial still. Not a photograph of the meeting, the builder, or the member.",
                    "alt_text": "Empty council committee room with microphones and blotters.",
                    "credit": "Desk stock / editorial illustration",
                    "policy_tag": "saatchi_editorial",
                    "documentary_incident": False,
                }
            ],
            "social": {
                "x": "HOLD. Defamation-sensitive. Do not post until legal has cleared the diary-gap wording.",
                "facebook": "HOLD. This draft is on the legal spike. No social until the desk and the lawyer agree the public-interest line.",
            },
        },
        {
            "id": uuid.UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            "headline": "Night-time A5 lane closures around Hinckley for a fortnight",
            "standfirst": "8pm–6am weekday resurfacing, signed diversion, daytime two-way with a 40mph limit through the site.",
            "slug": "a5-hinckley-night-closures",
            "verification_status": VerificationStatus.verified.value,
            "categories": ["Transport", "Hinckley"],
            "tags": ["a5", "national-highways", "diversion"],
            "source_links": [
                {
                    "url": "https://nationalhighways.co.uk/",
                    "label": "National Highways",
                    "note": "Works notice.",
                },
                {
                    "url": "https://www.leicestershire.gov.uk/",
                    "label": "Leicestershire County Council",
                    "note": "Diversion map / local highway authority.",
                },
            ],
            "spine_body": _body_roads(),
            "outlets": {
                "hinckley-desk": "Name the junction residents will actually sit in and the residential rat-runs the county has already asked drivers to avoid.",
                "conservative-post": "A short Midlands transport brief is enough nationally — dates, hours, and that daytime traffic still runs.",
            },
            "default_selected": ["hinckley-desk", "conservative-post"],
            "media": [
                {
                    "role": MediaRole.featured.value,
                    "placeholder_label": "Dual carriageway at dusk — no incident",
                    "caption": "Generic carriageway stock. Not crash photography, not a staged queue. Editorial illustration only.",
                    "alt_text": "UK dual carriageway at dusk with no incident visible.",
                    "credit": "Desk stock / editorial illustration",
                    "policy_tag": "saatchi_editorial",
                    "documentary_incident": False,
                }
            ],
            "social": {
                "x": "A5 around Hinckley: night-time lane closures for a fortnight from Monday, 8pm–6am weekdays. Daytime still two-way, 40mph through the site.",
                "facebook": "National Highways will close night-time lanes on the A5 around Hinckley for two weeks of resurfacing. Diversions will be signed; the county has asked drivers not to cut through housing streets.",
            },
        },
    ]

    for spec in drafts:
        selected = set(spec["default_selected"])
        draft = Draft(
            id=spec["id"],
            headline=spec["headline"],
            standfirst=spec["standfirst"],
            slug=spec["slug"],
            byline="Deepfold AI draft · desk copy",
            verification_status=spec["verification_status"],
            categories=spec["categories"],
            tags=spec["tags"],
            source_links=spec["source_links"],
            spine_body=spec["spine_body"],
        )
        db.add(draft)
        db.flush()
        for slug, graf in spec["outlets"].items():
            db.add(
                PublishTarget(
                    draft_id=draft.id,
                    outlet_id=outlets[slug].id,
                    selected=slug in selected,
                    local_graf=graf,
                )
            )
        for media in spec["media"]:
            db.add(MediaAsset(draft_id=draft.id, **media))
        for platform, copy in spec["social"].items():
            status = SocialStatus.held.value if "HOLD" in copy else SocialStatus.pending.value
            db.add(
                SocialPost(
                    draft_id=draft.id,
                    platform=SocialPlatform.x.value if platform == "x" else SocialPlatform.facebook.value,
                    body=copy,
                    status=status,
                )
            )
        apply_confidence(draft)
        write_audit(
            db,
            entity_type="draft",
            entity_id=str(draft.id),
            event_type="seeded",
            actor="system",
            payload={"slug": draft.slug, "verification": draft.verification_status},
        )


if __name__ == "__main__":
    seed_if_empty()
    print("Seed complete.")
