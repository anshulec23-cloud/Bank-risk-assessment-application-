"""
Agent 2: Classifier
Determines attack type and severity using rule-based heuristics + LLM explanation.
Populates state['classification'].
"""
from pipeline.state import PipelineState
from core.llm import llm_generate_sync


# Rule-based signature matching (fast, deterministic)
def _rule_based_classify(t: dict) -> tuple[str, str, float]:
    """Returns (attack_type, severity, confidence)"""
    temp = t.get("temperature", 0)
    pres = t.get("pressure", 0)
    flow = t.get("flow_rate", 999)
    volt = t.get("voltage", 230)

    # Variance check — suspiciously flat values → Spoofing
    if all([
        abs(temp - 65.0) < 0.5,
        abs(pres - 4.5)  < 0.05,
        abs(flow - 120.0)< 0.5,
    ]):
        return "Spoofing", "high", 0.88

    # Voltage drop only → Replay
    if volt < 200 and abs(temp - 65.0) < 5 and abs(flow - 120.0) < 15:
        return "Replay", "medium", 0.75

    # Extreme temperature + pressure → Physical Tamper or DoS
    if temp > 105 and pres > 8.5:
        return "PhysicalTamper", "critical", 0.91

    if temp > 85 and pres > 6.5:
        return "DoS", "high", 0.82

    # Preserve ambiguity instead of mislabeling unknown patterns as MitM
    return "Unknown", "low", 0.45


def classifier_node(state: PipelineState) -> PipelineState:
    if not state["anomaly"].get("is_anomaly"):
        state["classification"] = {
            "attack_type": "None",
            "severity": "none",
            "confidence": 0.0,
            "explanation": "No anomaly detected.",
        }
        return state

    t = state["telemetry"]
    attack_type, severity, confidence = _rule_based_classify(t)

    # LLM generates a plain-English explanation for non-technical stakeholders
    prompt = f"""
You are a cybersecurity analyst for an industrial control system.
A sensor anomaly has been detected with these readings:
  Temperature: {t['temperature']}°C (normal ~65°C)
  Pressure: {t['pressure']} bar (normal ~4.5 bar)
  Flow rate: {t['flow_rate']} L/min (normal ~120 L/min)
  Voltage: {t['voltage']} V (normal ~230 V)

Classified attack: {attack_type}, Severity: {severity}

In 2-3 plain English sentences, explain what this attack means for the facility
and why it is dangerous. Write for a non-technical CFO audience.
"""
    explanation = llm_generate_sync(prompt)

    state["classification"] = {
        "attack_type": attack_type,
        "severity":    severity,
        "confidence":  confidence,
        "explanation": explanation,
    }

    return state
