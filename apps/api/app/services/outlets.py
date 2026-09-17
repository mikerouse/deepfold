from __future__ import annotations

import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models import Draft, Outlet, OutletPackage, OutletPackageMember, PublishTarget
from app.schemas import OutletOut, PackageOut
from app.services.localisation import fallback_local_graf


def _package_out(package: OutletPackage) -> PackageOut:
    members = sorted(package.members, key=lambda m: (m.sort_order, m.outlet.name if m.outlet else ""))
    return PackageOut(
        id=package.id,
        name=package.name,
        slug=package.slug,
        region=package.region,
        county=package.county,
        description=package.description,
        outlets=[OutletOut.model_validate(m.outlet) for m in members if m.outlet],
    )


def search_outlets(
    db: Session,
    *,
    q: str | None = None,
    region: str | None = None,
    county: str | None = None,
    limit: int = 20,
) -> list[Outlet]:
    query = db.query(Outlet).filter(Outlet.active.is_(True))
    needle = (q or "").strip()
    if needle:
        like = f"%{needle}%"
        query = query.filter(
            or_(
                Outlet.name.ilike(like),
                Outlet.town.ilike(like),
                Outlet.slug.ilike(like),
                Outlet.county.ilike(like),
                Outlet.region.ilike(like),
            )
        )
    if region:
        query = query.filter(Outlet.region.ilike(region.strip()))
    if county:
        query = query.filter(Outlet.county.ilike(county.strip()))
    cap = max(1, min(limit, 50))
    return query.order_by(Outlet.name.asc()).limit(cap).all()


def list_packages(db: Session) -> list[PackageOut]:
    packages = (
        db.query(OutletPackage)
        .options(selectinload(OutletPackage.members).selectinload(OutletPackageMember.outlet))
        .order_by(OutletPackage.name.asc())
        .all()
    )
    return [_package_out(p) for p in packages]


def facets(db: Session) -> dict[str, list[str]]:
    regions = [
        row[0]
        for row in db.query(Outlet.region)
        .filter(Outlet.active.is_(True), Outlet.region != "")
        .distinct()
        .order_by(Outlet.region.asc())
        .all()
    ]
    counties = [
        row[0]
        for row in db.query(Outlet.county)
        .filter(Outlet.active.is_(True), Outlet.county != "")
        .distinct()
        .order_by(Outlet.county.asc())
        .all()
    ]
    return {"regions": regions, "counties": counties}


def _geo_tokens(draft: Draft) -> set[str]:
    geo = draft.geography or {}
    tokens: set[str] = set()
    for key in ("regions", "counties", "towns"):
        for item in geo.get(key) or []:
            if isinstance(item, str) and item.strip():
                tokens.add(item.strip().lower())
    for tag in draft.tags or []:
        if isinstance(tag, str) and tag.strip():
            tokens.add(tag.strip().lower())
    for category in draft.categories or []:
        if isinstance(category, str) and category.strip():
            tokens.add(category.strip().lower())
    return tokens


def suggest_for_draft(db: Session, draft: Draft, *, limit: int = 6) -> tuple[list[Outlet], list[PackageOut]]:
    tokens = _geo_tokens(draft)
    selected_ids = {t.outlet_id for t in draft.targets if t.selected}
    outlets = db.query(Outlet).filter(Outlet.active.is_(True)).all()
    scored: list[tuple[int, Outlet]] = []
    for outlet in outlets:
        if outlet.id in selected_ids:
            continue
        score = 0
        town = (outlet.town or "").lower()
        county = (outlet.county or "").lower()
        region = (outlet.region or "").lower()
        name = (outlet.name or "").lower()
        if town and town in tokens:
            score += 8
        if county and county in tokens:
            score += 5
        if region and region in tokens:
            score += 2
        if any(token in name or token in town for token in tokens if len(token) > 3):
            score += 1
        if outlet.default_selected:
            score += 1
        already = next((t for t in draft.targets if t.outlet_id == outlet.id), None)
        if already:
            score += 2
        if score > 0:
            scored.append((score, outlet))
    scored.sort(key=lambda row: (-row[0], row[1].name))
    suggested = [row[1] for row in scored[:limit]]

    packages = list_packages(db)
    matching_packages: list[PackageOut] = []
    for package in packages:
        county = (package.county or "").lower()
        region = (package.region or "").lower()
        if (county and county in tokens) or (region and region in tokens):
            matching_packages.append(package)
    if not matching_packages:
        matching_packages = packages[:2]
    return suggested, matching_packages


def ensure_targets(
    db: Session,
    draft: Draft,
    selected_ids: list[uuid.UUID],
    local_grafs: dict[str, str] | None = None,
) -> None:
    existing = {t.outlet_id: t for t in draft.targets}
    wanted = list(dict.fromkeys(selected_ids))
    missing = [oid for oid in wanted if oid not in existing]
    if missing:
        found = {o.id: o for o in db.query(Outlet).filter(Outlet.id.in_(missing)).all()}
        unknown = [str(oid) for oid in missing if oid not in found]
        if unknown:
            raise ValueError(f"Unknown outlet(s): {', '.join(unknown)}")
        for oid in missing:
            outlet = found[oid]
            graf = (local_grafs or {}).get(str(oid)) or fallback_local_graf(outlet, draft.headline)
            target = PublishTarget(
                draft_id=draft.id,
                outlet_id=oid,
                selected=True,
                local_graf=graf,
            )
            db.add(target)
            draft.targets.append(target)
            existing[oid] = target
    wanted_set = set(wanted)
    for target in draft.targets:
        target.selected = target.outlet_id in wanted_set
        if local_grafs and str(target.outlet_id) in local_grafs:
            target.local_graf = local_grafs[str(target.outlet_id)]
