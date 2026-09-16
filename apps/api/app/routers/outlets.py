from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Outlet
from app.schemas import OutletOut

router = APIRouter(prefix="/outlets", tags=["outlets"])


@router.get("", response_model=list[OutletOut])
def list_outlets(db: Session = Depends(get_db)):
    return db.query(Outlet).filter(Outlet.active.is_(True)).order_by(Outlet.name.asc()).all()
