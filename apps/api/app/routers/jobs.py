from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Job
from app.schemas import JobClaimIn, JobCompleteIn, JobOut
from app.services.jobs import claim_job, complete_job, load_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    status: str | None = None,
    kind: str | None = None,
    draft_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    if kind:
        query = query.filter(Job.kind == kind)
    if draft_id:
        query = query.filter(Job.draft_id == draft_id)
    return query.order_by(Job.created_at.asc()).limit(100).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = load_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/claim", response_model=JobOut)
def claim(job_id: uuid.UUID, body: JobClaimIn, db: Session = Depends(get_db)):
    job = load_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        claim_job(db, job, body.worker)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/complete", response_model=JobOut)
def complete(job_id: uuid.UUID, body: JobCompleteIn, db: Session = Depends(get_db)):
    job = load_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        complete_job(db, job, body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(job)
    return job
