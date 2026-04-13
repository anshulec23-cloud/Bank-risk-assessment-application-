from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from db.database import get_db
from db import models

router = APIRouter()


@router.get("/{incident_id}/nist", response_class=PlainTextResponse)
def get_nist_report(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not inc.nist_report:
        raise HTTPException(status_code=404, detail="Report not yet generated")
    return inc.nist_report


@router.get("/{incident_id}/credit-brief", response_class=PlainTextResponse)
def get_credit_brief(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not inc.credit_brief:
        raise HTTPException(status_code=404, detail="Credit brief not generated")
    return inc.credit_brief


@router.get("/{incident_id}/summary")
def get_report_summary(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {
        "incident_id":        inc.incident_id,
        "device_id":          inc.device_id,
        "attack_type":        inc.attack_type,
        "severity":           inc.severity,
        "total_exposure_usd": inc.total_exposure_usd,
        "credit_risk_flag":   inc.credit_risk_flag,
        "has_nist_report":    bool(inc.nist_report),
        "has_credit_brief":   bool(inc.credit_brief),
        "status":             inc.status,
        "created_at":         inc.created_at.isoformat() if inc.created_at else None,
    }
