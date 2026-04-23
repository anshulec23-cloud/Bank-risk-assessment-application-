from typing import TypedDict, Any


class PipelineState(TypedDict):
    telemetry:      dict[str, Any]   # raw MQTT payload
    anomaly:        dict[str, Any]   # Agent 1 output
    classification: dict[str, Any]   # Agent 2 output
    isolation:      dict[str, Any]   # Agent 3 output
    financial_risk: dict[str, Any]   # Agent 4 output
    report:         dict[str, Any]   # Agent 5 output


def empty_state(telemetry: dict) -> PipelineState:
    return PipelineState(
        telemetry=telemetry,
        anomaly={},
        classification={},
        isolation={},
        financial_risk={},
        report={},
    )
