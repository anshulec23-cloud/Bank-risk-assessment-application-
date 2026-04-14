"""
Agent 2: Classifier
Determines attack type and severity using rule-based heuristics.
Populates state['classification'].
"""
from pipeline.state import PipelineState


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

    # General high anomaly with mixed signals → MitM
    return "MitM", "medium", 0.65


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

    state["classification"] = {
        "attack_type": attack_type,
        "severity":    severity,
        "confidence":  confidence,
        "explanation": f"Detected {attack_type} attack - immediate action required.",
    }

    return state
