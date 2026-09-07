"""
Context builder module for FreightWise Stage 7 AI Agents + RAG layer.

Constructs AgentContext from Stage 2-6 pipeline outputs without altering,
recalculating, or mutating any numerical decision values.
"""

from typing import Any, Dict, List, Optional, Union

from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.provenance import create_provenance_record, attach_provenance_to_evidence


def _to_dict_safe(obj: Any) -> Optional[Dict[str, Any]]:
    """Safely convert a dataclass, model, or dict into a python dictionary without mutating data."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"raw_value": str(obj)}


def build_agent_context(
    stage2_output: Optional[Any] = None,
    stage3_output: Optional[Any] = None,
    stage4_output: Optional[Any] = None,
    stage5_output: Optional[Any] = None,
    stage6_output: Optional[Any] = None,
    evidence: Optional[List[EvidenceItem]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AgentContext:
    """
    Assemble an AgentContext from authoritative Stage 2-6 pipeline outputs.

    Rules:
    1. Preserves original numerical values strictly without recalculation.
    2. Preserves model names and model versions when available.
    3. Preserves explicit data scopes (e.g., GLOBAL_CONGESTION_PROXY).
    4. Preserves explicit unavailable statuses (e.g., DATA_UNAVAILABLE).
    5. Preserves feasibility status (FEASIBLE, INFEASIBLE, DATA_UNAVAILABLE).
    6. Preserves Stage 6 optimal plan.
    7. Keeps missing values as None.

    Args:
        stage2_output: Freight forecasting output (Stage 2).
        stage3_output: Delay / congestion prediction output (Stage 3).
        stage4_output: Vessel/port feasibility output (Stage 4).
        stage5_output: Cost / risk evaluation output (Stage 5).
        stage6_output: Optimization engine output (Stage 6).
        evidence: Optional list of pre-retrieved EvidenceItems.
        metadata: Optional metadata dictionary.

    Returns:
        Populated AgentContext object.
    """
    forecast_dict = _to_dict_safe(stage2_output)
    delay_dict = _to_dict_safe(stage3_output)

    # Handle stage3 output split if passed together or separate
    congestion_dict = None
    if stage3_output is not None:
        if isinstance(stage3_output, dict) and "congestion" in stage3_output:
            congestion_dict = _to_dict_safe(stage3_output["congestion"])
        elif hasattr(stage3_output, "congestion_index") or hasattr(stage3_output, "predicted_congestion_index"):
            congestion_dict = _to_dict_safe(stage3_output)
        elif isinstance(delay_dict, dict) and "predicted_congestion_index" in delay_dict:
            congestion_dict = {
                "predicted_congestion_index": delay_dict.get("predicted_congestion_index"),
                "high_congestion_risk": delay_dict.get("high_congestion_risk"),
                "data_scope": delay_dict.get("data_scope", "GLOBAL_CONGESTION_PROXY"),
            }

    feasibility_dict = _to_dict_safe(stage4_output)
    cost_dict = _to_dict_safe(stage5_output)
    optimization_dict = _to_dict_safe(stage6_output)

    context_evidence: List[EvidenceItem] = []
    if evidence:
        context_evidence.extend(evidence)

    # Automatically generate evidence items for authoritative pipeline outputs if provided
    if forecast_dict:
        prov = create_provenance_record(
            source="Stage2ForecastService",
            source_type="MODEL",
            stage="Stage 2",
            model_name=forecast_dict.get("model_name"),
            model_version=forecast_dict.get("model_version"),
            data_scope=forecast_dict.get("data_scope", "GLOBAL_FREIGHT"),
        )
        ev = EvidenceItem(
            evidence_id="ev-stage2-forecast",
            content=f"Stage 2 Freight Forecast: {forecast_dict.get('predicted_freight_rate')} {forecast_dict.get('unit', 'USD/day')} (Model: {forecast_dict.get('model_name')})",
            source="src/forecasting",
            source_type="FORECAST",
            relevance=1.0,
            provenance=prov,
        )
        context_evidence.append(ev)

    if delay_dict:
        prov = create_provenance_record(
            source="Stage3DelayService",
            source_type="MODEL",
            stage="Stage 3",
            model_name=delay_dict.get("model_name"),
            data_scope=delay_dict.get("data_scope", "EAST_COAST_INDIA"),
        )
        ev = EvidenceItem(
            evidence_id="ev-stage3-delay",
            content=f"Stage 3 Turnaround Delay Prediction: {delay_dict.get('predicted_turnaround_hours')} hours (Risk Score: {delay_dict.get('delay_risk_score')})",
            source="src/delays",
            source_type="DELAY",
            relevance=1.0,
            provenance=prov,
        )
        context_evidence.append(ev)

    if congestion_dict:
        prov = create_provenance_record(
            source="Stage3PortCongestionService",
            source_type="MODEL",
            stage="Stage 3",
            model_name=congestion_dict.get("model_name"),
            data_scope=congestion_dict.get("data_scope", "GLOBAL_CONGESTION_PROXY"),
        )
        ev = EvidenceItem(
            evidence_id="ev-stage3-congestion",
            content=f"Stage 3 Port Congestion Prediction: Index {congestion_dict.get('predicted_congestion_index')} (Scope: {congestion_dict.get('data_scope', 'GLOBAL_CONGESTION_PROXY')})",
            source="src/delays",
            source_type="CONGESTION",
            relevance=1.0,
            provenance=prov,
        )
        context_evidence.append(ev)

    if feasibility_dict:
        prov = create_provenance_record(
            source="Stage4FeasibilityEvaluator",
            source_type="RULE_ENGINE",
            stage="Stage 4",
            data_scope="EAST_COAST_INDIA",
        )
        status_val = feasibility_dict.get("status") or feasibility_dict.get("feasibility_status", "FEASIBLE")
        ev = EvidenceItem(
            evidence_id="ev-stage4-feasibility",
            content=f"Stage 4 Feasibility Evaluation: Status {status_val}",
            source="src/feasibility",
            source_type="FEASIBILITY",
            relevance=1.0,
            provenance=prov,
        )
        context_evidence.append(ev)

    if optimization_dict:
        prov = create_provenance_record(
            source="Stage6OptimizationEngine",
            source_type="OPTIMIZER",
            stage="Stage 6",
            data_scope="AUTHORIZED",
        )
        opt_status = optimization_dict.get("status") or optimization_dict.get("optimization_status", "OPTIMAL")
        ev = EvidenceItem(
            evidence_id="ev-stage6-optimization",
            content=f"Stage 6 Optimization Plan: Status {opt_status}",
            source="src/optimization",
            source_type="OPTIMIZATION",
            relevance=1.0,
            provenance=prov,
        )
        context_evidence.append(ev)

    return AgentContext(
        freight_forecast=forecast_dict,
        delay_prediction=delay_dict,
        congestion_prediction=congestion_dict,
        feasibility_result=feasibility_dict,
        cost_result=cost_dict,
        optimization_result=optimization_dict,
        evidence=context_evidence,
        metadata=dict(metadata) if metadata else {},
    )
