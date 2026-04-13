from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db import models

router = APIRouter()


@router.get("/")
def list_telemetry(
    device_id: str | None = None,
    limit: int = Query(100, le=500),
    anomaly_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(models.TelemetryEvent).order_by(models.TelemetryEvent.received_at.desc())
    if device_id:
        q = q.filter(models.TelemetryEvent.device_id == device_id)
    if anomaly_only:
        q = q.filter(models.TelemetryEvent.is_anomaly == True)
    return q.limit(limit).all()


@router.get("/latest")
def latest_per_device(db: Session = Depends(get_db)):
    """Returns the most recent telemetry row for each device."""
    from sqlalchemy import func
    subq = (
        db.query(
            models.TelemetryEvent.device_id,
            func.max(models.TelemetryEvent.id).label("max_id"),
        )
        .group_by(models.TelemetryEvent.device_id)
        .subquery()
    )
    rows = (
        db.query(models.TelemetryEvent)
        .join(subq, models.TelemetryEvent.id == subq.c.max_id)
        .all()
    )
    return rows


@router.get("/stats")
def telemetry_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total   = db.query(models.TelemetryEvent).count()
    anomaly = db.query(models.TelemetryEvent).filter_by(is_anomaly=True).count()
    avg_score = db.query(func.avg(models.TelemetryEvent.anomaly_score)).scalar() or 0.0
    return {
        "total_events": total,
        "anomaly_events": anomaly,
        "normal_events": total - anomaly,
        "anomaly_rate_pct": round((anomaly / total * 100) if total else 0, 2),
        "avg_anomaly_score": round(float(avg_score), 4),
    }
