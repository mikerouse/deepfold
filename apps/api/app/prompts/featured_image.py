from __future__ import annotations

from pathlib import Path
from typing import Any

BRIEF_VERSION = "featured_image_v1"
BRIEF_REPO_PATH = "apps/api/app/prompts/featured_image_v1.md"
BRIEF_PATH = Path(__file__).resolve().parent / "featured_image_v1.md"

DEFAULT_CREDIT = "Desk stock / editorial illustration"

# Seed / demo plates served by the desk from apps/desk/public/plates.
PLATE_URL_BY_SLUG = {
    "midlands-councils-40m-social-care": "/plates/civic-dusk.svg",
    "nuneaton-camphill-burglary-appeal": "/plates/suburban-daylight.svg",
    "cabinet-member-housebuilder-meeting": "/plates/empty-chamber.svg",
    "a5-hinckley-night-closures": "/plates/carriageway-dusk.svg",
}

_CRIME = ("crime", "burglar", "burglary", "police", "arrest", "assault", "theft", "stab")
_FIRE = ("fire", "blaze", "arson")
_CRASH = ("crash", "collision", "pile-up", "wreckage")
_ROADS = ("road", "a5", "highways", "closure", "transport", "carriageway", "diversion")
_MEETING = ("planning", "cabinet", "meeting", "housebuilder", "lobbying", "diary")
_CIVIC = ("council", "budget", "care", "social", "shire", "county")


def load_base_brief() -> str:
    return BRIEF_PATH.read_text(encoding="utf-8").strip()


def _place(geography: dict[str, Any] | None) -> str:
    geo = geography or {}
    towns = [t for t in (geo.get("towns") or []) if t]
    counties = [c for c in (geo.get("counties") or []) if c]
    if counties and towns:
        return f"{towns[0]}, {counties[0]}"
    if counties:
        return counties[0]
    if towns:
        return towns[0]
    regions = [r for r in (geo.get("regions") or []) if r]
    if regions:
        return regions[0]
    return "the UK"


def _blob(headline: str, standfirst: str, spine: str, categories: list[Any] | None) -> str:
    cats = " ".join(str(c) for c in (categories or []))
    return " ".join([headline or "", standfirst or "", (spine or "")[:400], cats]).lower()


def story_specific_scene(
    headline: str,
    standfirst: str = "",
    spine: str = "",
    geography: dict[str, Any] | None = None,
    categories: list[Any] | None = None,
) -> str:
    """Heuristic 1–3 sentences. Generic editorial place-type; never the incident."""
    place = _place(geography)
    text = _blob(headline, standfirst, spine, categories)

    if any(word in text for word in _CRIME):
        return (
            f"A quiet residential street in {place} in ordinary British daylight: "
            "brick houses, parked cars, a pavement and a pale sky. "
            "No incident, no police tape, no identifiable address, no reconstructed crime."
        )
    if any(word in text for word in _FIRE):
        return (
            f"Civic rooftops and a calm skyline in {place} under natural light. "
            "No flames, no smoke, no named building on fire."
        )
    if any(word in text for word in _CRASH):
        return (
            f"A UK dual carriageway near {place} in fading light: wet tarmac, cat's eyes, empty of incident. "
            "No wreckage, no staged queue, no emergency lights."
        )
    if any(word in text for word in _ROADS):
        return (
            f"A UK dual carriageway at dusk near {place}, landscape, natural light: "
            "wet tarmac receding, a pale sky, no crash and no queue. One quiet idea of a road at rest."
        )
    if any(word in text for word in _MEETING):
        return (
            f"An empty, lights-on committee chamber in a {place} civic building: "
            "microphones, blotters, vacant chairs. No people, no meeting in progress, no identifiable faces."
        )
    if any(word in text for word in _CIVIC):
        return (
            f"A Midlands civic building in {place} at dusk: stone facade, lamps on, empty forecourt, a flagpole. "
            "Mood of local government. Not a named meeting, not a specific councillor."
        )

    lead = (standfirst or headline or "everyday civic life").strip().split(".")[0]
    return (
        f"A landscape editorial still of everyday civic life in {place}, natural British light. "
        f"One quiet idea suggested by: {lead}. "
        "No text, no logos, no reconstructed incident, no identifiable private address."
    )


def featured_image_payload(draft: Any) -> dict[str, Any]:
    return {
        "headline": draft.headline,
        "slug": getattr(draft, "slug", ""),
        "standfirst": getattr(draft, "standfirst", "") or "",
        "brief_version": BRIEF_VERSION,
        "brief_path": BRIEF_REPO_PATH,
        "base_brief": load_base_brief(),
        "story_specific_scene": story_specific_scene(
            headline=draft.headline,
            standfirst=getattr(draft, "standfirst", "") or "",
            spine=getattr(draft, "spine_body", "") or "",
            geography=getattr(draft, "geography", None) or {},
            categories=getattr(draft, "categories", None),
        ),
        "geography": getattr(draft, "geography", None) or {},
        "documentary_safe": True,
    }


def plate_url_for(slug: str) -> str:
    return PLATE_URL_BY_SLUG.get(slug, "/plates/civic-dusk.svg")
