"""
LangGraph Pipeline
==================
Directed graph: Detector → Classifier → [Isolator ‖ RiskQuantifier] → Reporter

The Isolator and RiskQuantifier run sequentially (not parallel) because
LangGraph's StateGraph is synchronous per node; parallelism would require
a fan-out which adds complexity without benefit for a 24h hackathon MVP.
"""
from langgraph.graph import StateGraph, END

from pipeline.state import PipelineState, empty_state
from agents.detector      import detector_node
from agents.classifier    import classifier_node
from agents.isolator      import isolator_node
from agents.risk_quantifier import risk_quantifier_node
from agents.reporter      import reporter_node


def _should_continue(state: PipelineState) -> str:
    """
    Conditional edge after Detector.
    If no anomaly: skip directly to END (no LLM calls, no DB writes).
    """
    return "classify" if state["anomaly"].get("is_anomaly") else "end"


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("detect",        detector_node)
    graph.add_node("classify",      classifier_node)
    graph.add_node("isolate",       isolator_node)
    graph.add_node("quantify_risk", risk_quantifier_node)
    graph.add_node("generate_report",        reporter_node)

    graph.set_entry_point("detect")

    graph.add_conditional_edges(
        "detect",
        _should_continue,
        {"classify": "classify", "end": END},
    )
    graph.add_edge("classify",      "isolate")
    graph.add_edge("isolate",       "quantify_risk")
    graph.add_edge("quantify_risk", "generate_report")
    graph.add_edge("generate_report",        END)

    return graph.compile()


# Module-level compiled graph — reused across requests
pipeline = build_graph()


def run_pipeline(telemetry: dict) -> PipelineState:
    """
    Entry point for the FastAPI layer.
    Returns the fully populated PipelineState.
    """
    initial = empty_state(telemetry)
    return pipeline.invoke(initial)
