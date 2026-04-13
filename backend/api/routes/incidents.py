from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db import models

router = APIRouter()


@router.get("/")
def list_incidents(
    limit: int = Query(50, le=200),
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Incident).order_by(models.Incident.created_at.desc())
    if severity:
        q = q.filter(models.Incident.severity == severity)
    return q.limit(limit).all()


@router.get("/summary")
def incident_summary(db: Session = Depends(get_db)):
    total     = db.query(models.Incident).count()
    critical  = db.query(models.Incident).filter_by(severity="critical").count()
    high      = db.query(models.Incident).filter_by(severity="high").count()
    open_inc  = db.query(models.Incident).filter_by(status="OPEN").count()

    from sqlalchemy import func
    total_exposure = db.query(func.sum(models.Incident.total_exposure_usd)).scalar() or 0.0

    return {
        "total_incidents": total,
        "critical": critical,
        "high": high,
        "open": open_inc,
        "total_exposure_usd": round(total_exposure, 2),
    }


@router.get("/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.patch("/{incident_id}/resolve")
def resolve_incident(incident_id: str, db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    inc.status = "RESOLVED"
    inc.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "resolved", "incident_id": incident_id}
