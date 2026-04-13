"""
Agent 4: Risk Quantifier
Calculates the financial blast radius of the detected attack:
  - Downtime cost
  - SLA penalty
  - Regulatory fine (NERC CIP / NIS2 scale)
  - Credit risk flag for lending institutions

Methodology:
  downtime_cost    = hourly_cost[device_type] × estimated_downtime_hours[severity]
  sla_penalty      = downtime_cost × 0.15   (industry standard ~15% of downtime)
  regulatory_fine  = lookup table by severity (NERC CIP schedule)
  total_exposure   = sum of all three
  credit_risk_flag = bucketed from total_exposure

Populates state['financial_risk'].
"""
from pipeline.state import PipelineState
from core.config import settings

# Hourly downtime cost by device type (USD) — sourced from industry reports
HOURLY_COST = {
    "power_plant":     settings.COST_POWER_PLANT,
    "water_treatment": settings.COST_WATER_TREATMENT,
    "factory":         settings.COST_FACTORY,
    "oil_refinery":    settings.COST_OIL_REFINERY,
}

# Estimated downtime hours per severity level
DOWNTIME_HOURS = {
    "none":     0.0,
    "low":      settings.DOWNTIME_HOURS_LOW,
    "medium":   settings.DOWNTIME_HOURS_MEDIUM,
    "high":     settings.DOWNTIME_HOURS_HIGH,
    "critical": settings.DOWNTIME_HOURS_CRITICAL,
}

# NERC CIP / NIS2-aligned regulatory fine estimates (USD)
REGULATORY_FINES = {
    "none":     0,
    "low":      25_000,
    "medium":   150_000,
    "high":     500_000,
    "critical": 1_500_000,
}

# Credit risk thresholds (USD total exposure)
def _credit_risk_flag(total_exposure: float) -> str:
    if total_exposure < 50_000:
        return "NORMAL"
    elif total_exposure < 500_000:
        return "ELEVATED"
    elif total_exposure < 2_000_000:
        return "HIGH"
    return "CRITICAL"


def risk_quantifier_node(state: PipelineState) -> PipelineState:
    anomaly = state["anomaly"]
    classification = state["classification"]
    severity = classification.get("severity", "none")

    device_type   = anomaly.get("device_type", "factory")
    hourly_cost   = HOURLY_COST.get(device_type, settings.COST_DEFAULT)
    downtime_hrs  = DOWNTIME_HOURS.get(severity, 0.0)

    downtime_cost   = round(hourly_cost * downtime_hrs, 2)
    sla_penalty     = round(downtime_cost * 0.15, 2)
    regulatory_fine = REGULATORY_FINES.get(severity, 0)
    total_exposure  = round(downtime_cost + sla_penalty + regulatory_fine, 2)
    credit_flag     = _credit_risk_flag(total_exposure)

    state["financial_risk"] = {
        "device_type":          device_type,
        "hourly_cost_usd":      hourly_cost,
        "estimated_downtime_h": downtime_hrs,
        "downtime_cost_usd":    downtime_cost,
        "sla_penalty_usd":      sla_penalty,
        "regulatory_fine_usd":  regulatory_fine,
        "total_exposure_usd":   total_exposure,
        "credit_risk_flag":     credit_flag,
    }

    return state
