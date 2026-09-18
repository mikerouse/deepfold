from __future__ import annotations

from pathlib import Path
from typing import Any

CP_VERSION = "draft_article_conservative_post_v1"
LOCAL_VERSION = "draft_article_local_v1"
CP_REPO_PATH = "apps/api/app/prompts/draft_article_conservative_post_v1.md"
LOCAL_REPO_PATH = "apps/api/app/prompts/draft_article_local_v1.md"
PROMPTS_DIR = Path(__file__).resolve().parent

HOUSE_STYLE_LABELS = {
    CP_VERSION: "Conservative Post v1",
    LOCAL_VERSION: "Local craft v1",
}

# Patriotic national title. Conservative Post is one outlet, not the product.
CP_SLUGS = {"conservative-post"}


def load_brief(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def _norm(value: Any) -> str:
    return (value or "").strip().lower().replace("_", "-")


def is_patriotic_national_title(outlet: Any | None) -> bool:
    """Conservative Post / patriotic national → CP master prompt.

    Matches the seeded Conservative Post slug/name, and a National-region
    title whose name or slug is patriotic / Conservative Post. Does not
    treat ordinary local desks as national.
    """
    if outlet is None:
        return False
    slug = _norm(getattr(outlet, "slug", ""))
    name = _norm(getattr(outlet, "name", ""))
    region = _norm(getattr(outlet, "region", ""))
    if slug in CP_SLUGS or slug.startswith("conservative-post"):
        return True
    if "conservative post" in name:
        return True
    if region == "national" and ("patriotic" in name or "patriotic" in slug or "conservative" in name):
        return True
    return False


def selected_outlets(draft: Any) -> list[Any]:
    outlets: list[Any] = []
    for target in getattr(draft, "targets", None) or []:
        if getattr(target, "selected", False) and getattr(target, "outlet", None):
            outlets.append(target.outlet)
    return outlets


def primary_outlet(draft: Any) -> Any | None:
    """Primary title for the spine.

    If Conservative Post / patriotic national is among the selected titles,
    that is the primary (the spine is the national piece; locals get grafs
    from localize_outlets). Otherwise the first selected outlet. Unknown
    or unselected → None (caller defaults to local craft).
    """
    outlets = selected_outlets(draft)
    for outlet in outlets:
        if is_patriotic_national_title(outlet):
            return outlet
    return outlets[0] if outlets else None


def brief_choice(draft: Any) -> tuple[str, str, str]:
    """Return (brief_version, brief_path, house_style_label).

    Conservative Post / patriotic national → CP master prompt.
    Redditch Standard, Bromsgrove Standard, Worcester Observer, other locals,
    and unknown / no selected title → local craft (no CP politics).
    """
    outlet = primary_outlet(draft)
    if is_patriotic_national_title(outlet):
        return CP_VERSION, CP_REPO_PATH, HOUSE_STYLE_LABELS[CP_VERSION]
    return LOCAL_VERSION, LOCAL_REPO_PATH, HOUSE_STYLE_LABELS[LOCAL_VERSION]


def _outlet_stub(outlet: Any | None) -> dict[str, str] | None:
    if outlet is None:
        return None
    return {
        "name": getattr(outlet, "name", "") or "",
        "slug": getattr(outlet, "slug", "") or "",
        "region": getattr(outlet, "region", "") or "",
    }


def draft_article_payload(draft: Any) -> dict[str, Any]:
    version, path, label = brief_choice(draft)
    standfirst = getattr(draft, "standfirst", "") or ""
    spine = getattr(draft, "spine_body", "") or ""
    return {
        "headline": draft.headline,
        "slug": getattr(draft, "slug", "") or "",
        "standfirst": standfirst,
        "abstract": standfirst,
        "spine": spine,
        "spine_body": spine,
        "geography": getattr(draft, "geography", None) or {},
        "brief_version": version,
        "brief_path": path,
        "base_brief": load_brief(Path(path).name),
        "house_style_label": label,
        "primary_outlet": _outlet_stub(primary_outlet(draft)),
        "categories": list(getattr(draft, "categories", None) or []),
        "tags": list(getattr(draft, "tags", None) or []),
        "source_links": list(getattr(draft, "source_links", None) or []),
        "verification_status": getattr(draft, "verification_status", None) or "",
    }
