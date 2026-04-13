"""
Agent 5: Reporter
Uses LLM to generate:
  1. NIST SP 800-61 structured incident report (for security / compliance team)
  2. Bank credit risk brief (for lending institution)

Populates state['report'].
"""
import uuid
from datetime import datetime, timezone
from pipeline.state import PipelineState
from core.llm import llm_generate_sync


def _nist_report_prompt(state: PipelineState) -> str:
    t = state["telemetry"]
    a = state["anomaly"]
    c = state["classification"]
    iso = state["isolation"]
    fr = state["financial_risk"]

    return f"""
Generate a concise NIST SP 800-61 incident report for the following ICS security incident.
Use the exact section headings below. Keep each section to 2-4 sentences.

INCIDENT DETAILS:
  Device ID:     {a['device_id']}
  Device Type:   {a['device_type']}
  Location:      {a['location']}
  Attack Type:   {c['attack_type']}
  Severity:      {c['severity'].upper()}
  Confidence:    {round(c['confidence']*100, 1)}%
  Anomaly Score: {a['anomaly_score']}
  Isolation:     {iso['action_taken']}
  Timestamp:     {datetime.now(timezone.utc).isoformat()}

TELEMETRY AT TIME OF DETECTION:
  Temperature: {t['temperature']}°C | Pressure: {t['pressure']} bar
  Flow Rate: {t['flow_rate']} L/min | Voltage: {t['voltage']} V

FINANCIAL EXPOSURE:
  Downtime Cost: ${fr['downtime_cost_usd']:,.0f}
  SLA Penalty:   ${fr['sla_penalty_usd']:,.0f}
  Regulatory Fine: ${fr['regulatory_fine_usd']:,.0f}
  Total Exposure:  ${fr['total_exposure_usd']:,.0f}

REQUIRED SECTIONS:
1. INCIDENT SUMMARY
2. INDICATORS OF COMPROMISE
3. IMPACT ASSESSMENT
4. CONTAINMENT ACTIONS TAKEN
5. RECOMMENDED NEXT STEPS
6. REGULATORY COMPLIANCE NOTES (NERC CIP / IEC 62443)
"""


def _credit_brief_prompt(state: PipelineState) -> str:
    a = state["anomaly"]
    c = state["classification"]
    fr = state["financial_risk"]

    return f"""
Write a brief credit risk advisory (3-4 paragraphs) for a bank that has issued
infrastructure financing to the affected facility.

CONTEXT:
  Facility Type: {a['device_type'].replace('_',' ').title()}
  Attack Type:   {c['attack_type']} | Severity: {c['severity'].upper()}
  Total Financial Exposure: ${fr['total_exposure_usd']:,.0f}
  Credit Risk Flag: {fr['credit_risk_flag']}
  Estimated Downtime: {fr['estimated_downtime_h']} hours

Cover: current risk status, potential impact on debt-service capacity,
recommended lender actions, and whether covenant review is advised.
Write in professional banking language. Do not use bullet points.
"""


def reporter_node(state: PipelineState) -> PipelineState:
    if not state["anomaly"].get("is_anomaly"):
        state["report"] = {
            "report_id":   None,
            "nist_report": None,
            "credit_brief": None,
        }
        return state

    report_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

    nist_report  = llm_generate_sync(_nist_report_prompt(state))
    credit_brief = llm_generate_sync(_credit_brief_prompt(state))

    state["report"] = {
        "report_id":    report_id,
        "nist_report":  nist_report,
        "credit_brief": credit_brief,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    return state
