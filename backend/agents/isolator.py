"""
Agent 3: Isolator
Decides whether to isolate the device and triggers micro-segmentation.
Physical safety constraint: isolation NEVER shuts down the device —
it cuts its network access only, leaving physical control intact.
Populates state['isolation'].
"""
from pipeline.state import PipelineState

# Severity levels that trigger automatic isolation
AUTO_ISOLATE_SEVERITIES = {"high", "critical"}


def isolator_node(state: PipelineState) -> PipelineState:
    classification = state["classification"]
    anomaly = state["anomaly"]
    severity = classification.get("severity", "none")

    should_isolate = (
        anomaly.get("is_anomaly") and
        severity in AUTO_ISOLATE_SEVERITIES
    )

    action_log = []

    if should_isolate:
        device_id = anomaly["device_id"]
        # The actual MQTT publish happens in api/main.py via the global mqtt_listener
        # Here we record the decision; the pipeline executor handles the side-effect
        action_log.append(f"Network isolation command queued for {device_id}")
        action_log.append("Physical operations remain unaffected (zero-trust boundary)")
        action_log.append(f"Device policy engine on {device_id} notified to reject external commands")

    state["isolation"] = {
        "should_isolate":   should_isolate,
        "device_id":        anomaly["device_id"],
        "action_taken":     "NETWORK_ISOLATED" if should_isolate else "MONITOR_ONLY",
        "action_log":       action_log,
        "severity_trigger": severity,
    }

    return state
