"""
Agent 1: Detector
Runs the Random Forest model on raw telemetry.
Populates state['anomaly'].
"""
from pipeline.state import PipelineState
from ml.model import predict


def detector_node(state: PipelineState) -> PipelineState:
    t = state["telemetry"]

    result = predict(
        temperature=t["temperature"],
        pressure=t["pressure"],
        flow_rate=t["flow_rate"],
        voltage=t["voltage"],
    )

    state["anomaly"] = {
        "device_id":    t["device_id"],
        "device_type":  t.get("device_type", "factory"),
        "location":     t.get("location", "Unknown"),
        "anomaly_score": result["anomaly_score"],
        "is_anomaly":    result["is_anomaly"],
        "feature_importances": result["feature_importances"],
    }

    return state
