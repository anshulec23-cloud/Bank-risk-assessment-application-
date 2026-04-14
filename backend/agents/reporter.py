"""
Agent 5: Reporter
Generates NIST incident report and bank credit risk brief.
Populates state['report'].
"""
import uuid
from datetime import datetime, timezone
from pipeline.state import PipelineState


def reporter_node(state: PipelineState) -> PipelineState:
    if not state["anomaly"].get("is_anomaly"):
        state["report"] = {
            "report_id":   None,
            "nist_report": None,
            "credit_brief": None,
        }
        return state
    
    report_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    
    a = state["anomaly"]
    c = state["classification"]
    fr = state["financial_risk"]

    nist_report = f"""INCIDENT SUMMARY
Device: {a['device_id']} ({a['device_type']})
Location: {a['location']}
Attack Type: {c['attack_type']}
Severity: {c['severity'].upper()}
Anomaly Score: {a['anomaly_score']}

IMPACT ASSESSMENT
Financial Exposure: ${fr.get('total_exposure_usd', 0):,.0f}
Credit Risk: {fr.get('credit_risk_flag', 'NORMAL')}

CONTAINMENT ACTIONS
{state['isolation'].get('action_taken', 'MONITOR_ONLY')}
"""

    credit_brief = f"""CREDIT RISK ADVISORY

Facility: {a['device_type'].replace('_', ' ').title()}
Attack: {c['attack_type']} - Severity: {c['severity'].upper()}
Total Exposure: ${fr.get('total_exposure_usd', 0):,.0f}
Risk Flag: {fr.get('credit_risk_flag', 'NORMAL')}

Recommendation: Review cyber insurance coverage and endpoint protection.
"""

    state["report"] = {
        "report_id":    report_id,
        "nist_report":  nist_report,
        "credit_brief": credit_brief,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    return state