from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from db.database import get_db
from db import models
from core.llm import llm_generate_sync

router = APIRouter()


def _report_is_stale(text: str | None) -> bool:
    return not text or text.startswith("[LLM") or "| Severity:" in text


def _build_nist_prompt(inc: models.Incident) -> str:
    return f"""
Generate a concise NIST SP 800-61 incident report for the following ICS security incident.

INCIDENT DETAILS:
  Device ID: {inc.device_id}
  Location: Unknown
  Attack Type: {inc.attack_type}
  Severity: {inc.severity.upper()}
  Total Exposure: ${inc.total_exposure_usd:,.0f}
"""


def _build_credit_prompt(inc: models.Incident) -> str:
    return f"""
Write a brief credit risk advisory for a bank.

CONTEXT:
  Facility Type: {inc.device_id}
  Attack Type: {inc.attack_type}
  Severity: {inc.severity.upper()}
  Total Financial Exposure: ${inc.total_exposure_usd:,.0f}
  Credit Risk Flag: {inc.credit_risk_flag}
"""


@router.get("/{incident_id}/nist", response_class=PlainTextResponse)
def get_nist_report(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if _report_is_stale(inc.nist_report):
        inc.nist_report = llm_generate_sync(_build_nist_prompt(inc))
        db.commit()
    return inc.nist_report


@router.get("/{incident_id}/credit-brief", response_class=PlainTextResponse)
def get_credit_brief(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).filter_by(incident_id=incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if _report_is_stale(inc.credit_brief):
        inc.credit_brief = llm_generate_sync(_build_credit_prompt(inc))
        db.commit()
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
