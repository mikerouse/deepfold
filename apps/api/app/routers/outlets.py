from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Draft, PublishTarget
from app.schemas import OutletFacetsOut, OutletOut, OutletSuggestOut, PackageOut
from app.services.outlets import facets, list_packages, search_outlets, suggest_for_draft

router = APIRouter(prefix="/outlets", tags=["outlets"])


@router.get("", response_model=list[OutletOut])
def list_outlets(
    q: str | None = Query(default=None),
    region: str | None = None,
    county: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return search_outlets(db, q=q, region=region, county=county, limit=limit)


@router.get("/packages", response_model=list[PackageOut])
def packages(db: Session = Depends(get_db)):
    return list_packages(db)


@router.get("/facets", response_model=OutletFacetsOut)
def outlet_facets(db: Session = Depends(get_db)):
    return OutletFacetsOut(**facets(db))


@router.get("/suggest", response_model=OutletSuggestOut)
def suggest(draft_id: uuid.UUID, db: Session = Depends(get_db)):
    draft = (
        db.query(Draft)
        .options(selectinload(Draft.targets).selectinload(PublishTarget.outlet))
        .filter(Draft.id == draft_id)
        .one_or_none()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    outlets, packages = suggest_for_draft(db, draft)
    return OutletSuggestOut(outlets=[OutletOut.model_validate(o) for o in outlets], packages=packages)
