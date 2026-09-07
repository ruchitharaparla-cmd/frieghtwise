"""Stage 7.8 FreightWise End-to-End AI/RAG Integration Service.

Provides FreightWiseAIService as the unified, high-level entry point for the complete
Stage 7 AI/RAG stack, integrating:

    - Stage 7.1: Safety contracts and context binding (build_agent_context)
    - Stage 7.2: RAG document ingestion (KnowledgeBaseIngestionPipeline, used separately)
    - Stage 7.3: RAG retrieval (RAGRetriever)
    - Stage 7.4: Market Analyst Agent (MarketAnalystService)
    - Stage 7.5: Risk Analyst Agent (RiskAnalystService)
    - Stage 7.6: Procurement Strategy Agent (ProcurementStrategyService)
    - Stage 7.7: Multi-Agent Orchestrator (MultiAgentOrchestrator)

Usage:
    ai_service = FreightWiseAIService(is_testing=True)
    response = ai_service.query_ai_assistant(
        query="What are the risks for this voyage?",
        stage2_output=my_forecast_result,
        stage3_output=my_delay_result,
        stage4_output=my_feasibility_result,
        stage5_output=my_cost_result,
        stage6_output=my_optimization_result,
    )

Architecture:
    User query + Stage 2-6 outputs
        |
        v
    build_agent_context()  <-- Stage 7.1 context binding
        |
        v
    MultiAgentOrchestrator.orchestrate()  <-- Stage 7.7
        |
        +--> MarketAnalystService.analyze() + RAGRetriever  <-- Stage 7.4 + 7.3
        +--> RiskAnalystService.analyze()   + RAGRetriever  <-- Stage 7.5 + 7.3
        +--> ProcurementStrategyService.analyze() + RAGRetriever  <-- Stage 7.6 + 7.3
        |
        v
    MultiAgentOrchestrationResponse
        |
        v
    FreightWiseAIServiceResponse

Safety Contracts (non-negotiable):
    - AI layer is DOWNSTREAM of Stage 2-6 authoritative numerical pipeline.
    - AI agents NEVER make freight predictions, cost calculations, or optimization decisions.
    - All authoritative numerical outputs are immutable and passed through unchanged.
    - DATA_UNAVAILABLE values are preserved exactly.
    - GLOBAL_CONGESTION_PROXY scope boundary is preserved and never reinterpreted.
    - No fallback to deterministic fake responses in production mode.
    - If all LLM providers are unavailable, FreightWiseAIServiceResponse.status is
      'ALL_PROVIDERS_UNAVAILABLE' with explicit message. No silent fake data.
"""

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import uuid

from src.agents.context import build_agent_context
from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.orchestrator.contracts import MultiAgentOrchestrationRequest, MultiAgentOrchestrationResponse
from src.agents.orchestrator.service import MultiAgentOrchestrator


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_service_id() -> str:
    return f"fw_ai_{uuid.uuid4().hex[:12]}"


@dataclass
class FreightWiseAIServiceResponse:
    """Unified response from FreightWiseAIService.

    Wraps the MultiAgentOrchestrationResponse and adds service-level metadata
    for end-to-end traceability.

    Fields:
        service_id: Unique request identifier for this AI service call.
        query: Original user query.
        orchestration_response: Full multi-agent orchestration response.
        synthesized_answer: Top-level narrative synthesis (mirrors orchestration_response.synthesized_answer).
        status: Overall service status.
        timestamp: UTC timestamp of this service response.
        pipeline_context_summary: Summary of Stage 2-6 numerical inputs (read-only, not mutated).
        metadata: Extra metadata.
    """

    service_id: str = field(default_factory=_generate_service_id)
    query: str = ""
    orchestration_response: Optional[MultiAgentOrchestrationResponse] = None
    synthesized_answer: str = ""
    status: str = "SUCCESS"
    # 'SUCCESS', 'PARTIAL_SUCCESS', 'ALL_PROVIDERS_UNAVAILABLE', 'VALIDATION_FAILED', 'ERROR'
    timestamp: str = field(default_factory=_utc_timestamp)
    pipeline_context_summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "query": self.query,
            "orchestration_response": self.orchestration_response.to_dict() if self.orchestration_response else None,
            "synthesized_answer": self.synthesized_answer,
            "status": self.status,
            "timestamp": self.timestamp,
            "pipeline_context_summary": dict(self.pipeline_context_summary),
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class FreightWiseAIService:
    """Stage 7.8 End-to-End AI/RAG Integration Service.

    Provides a single unified entry point for FreightWise AI capabilities
    that operates strictly DOWNSTREAM of the authoritative Stage 2-6 pipeline.

    This service:
        1. Accepts Stage 2-6 numerical outputs as authoritative inputs.
        2. Binds them into AgentContext via build_agent_context (Stage 7.1).
        3. Dispatches to the Multi-Agent Orchestrator (Stage 7.7),
           which internally uses Market/Risk/Procurement Agents (7.4-7.6)
           and RAG Retrieval (7.3).
        4. Returns a FreightWiseAIServiceResponse with full provenance.

    The AI layer NEVER:
        - Makes freight rate predictions.
        - Calculates costs or risk scores.
        - Overrides Stage 6 CP-SAT solver optimization results.
        - Invents vessel specs, port specs, or numerical values.
        - Silently falls back to deterministic fake responses in production.
        - Reinterprets GLOBAL_CONGESTION_PROXY as Indian port congestion.

    Attributes:
        orchestrator: MultiAgentOrchestrator instance.
        is_testing: If True, agent services use deterministic TEST-ONLY models.
    """

    def __init__(
        self,
        orchestrator: Optional[MultiAgentOrchestrator] = None,
        is_testing: bool = False,
    ):
        self.is_testing = is_testing
        self.orchestrator = orchestrator or MultiAgentOrchestrator(is_testing=is_testing)

    def _build_context_summary(self, context: AgentContext) -> Dict[str, Any]:
        """Build a read-only summary of Stage 2-6 numerical inputs for response metadata.

        This summary is informational only. The original context values are immutable.
        """
        summary: Dict[str, Any] = {}
        if context.freight_forecast is not None:
            rate = context.freight_forecast.get("predicted_freight_rate") or context.freight_forecast.get("predicted_rate")
            summary["stage2_freight_rate"] = rate
            summary["stage2_model"] = context.freight_forecast.get("model_name", "UNKNOWN")
        if context.delay_prediction is not None:
            hrs = context.delay_prediction.get("predicted_delay_hours") or context.delay_prediction.get("predicted_turnaround_hours")
            summary["stage3_delay_hours"] = hrs
        if context.congestion_prediction is not None:
            idx = context.congestion_prediction.get("predicted_congestion_index")
            summary["stage3_congestion_index"] = idx
            summary["stage3_congestion_scope"] = context.congestion_prediction.get("data_scope", "GLOBAL_CONGESTION_PROXY")
        if context.feasibility_result is not None:
            summary["stage4_feasibility"] = (
                context.feasibility_result.get("status")
                or context.feasibility_result.get("feasibility_status")
            )
        if context.cost_result is not None:
            summary["stage5_cost_available"] = True
        if context.optimization_result is not None:
            summary["stage6_optimization_status"] = (
                context.optimization_result.get("status")
                or context.optimization_result.get("optimization_status")
            )
        return summary

    def query_ai_assistant(
        self,
        query: str,
        stage2_output: Optional[Any] = None,
        stage3_output: Optional[Any] = None,
        stage4_output: Optional[Any] = None,
        stage5_output: Optional[Any] = None,
        stage6_output: Optional[Any] = None,
        context: Optional[AgentContext] = None,
        enable_market: bool = True,
        enable_risk: bool = True,
        enable_procurement: bool = True,
        retrieval_query: Optional[str] = None,
        max_evidence_items: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FreightWiseAIServiceResponse:
        """Execute a full AI/RAG-assisted analytical query across the FreightWise pipeline.

        Accepts authoritative Stage 2-6 outputs (or a pre-built AgentContext),
        binds them into AgentContext, dispatches to the Multi-Agent Orchestrator,
        and returns a structured FreightWiseAIServiceResponse.

        Args:
            query: User question or analytical query (required, non-empty).
            stage2_output: Stage 2 freight forecasting output.
            stage3_output: Stage 3 delay/congestion prediction output.
            stage4_output: Stage 4 vessel/port feasibility output.
            stage5_output: Stage 5 cost/risk evaluation output.
            stage6_output: Stage 6 CP-SAT optimization output.
            context: Optional pre-built AgentContext (overrides stage2_6 outputs if provided).
            enable_market: Whether to invoke Market Analyst Agent.
            enable_risk: Whether to invoke Risk Analyst Agent.
            enable_procurement: Whether to invoke Procurement Strategy Agent.
            retrieval_query: Optional override for RAG retrieval query. Defaults to query.
            max_evidence_items: Maximum evidence items per agent RAG retrieval.
            metadata: Optional metadata to include in response.

        Returns:
            FreightWiseAIServiceResponse with multi-agent synthesis, evidence, and provenance.

        Raises:
            ValueError: If query is empty or no agents are enabled.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("FreightWiseAIService: query cannot be empty or whitespace-only.")
        if not any([enable_market, enable_risk, enable_procurement]):
            raise ValueError("FreightWiseAIService: at least one agent must be enabled.")

        # Build or use provided AgentContext
        if context is not None:
            bound_context = copy.deepcopy(context)
        else:
            bound_context = build_agent_context(
                stage2_output=stage2_output,
                stage3_output=stage3_output,
                stage4_output=stage4_output,
                stage5_output=stage5_output,
                stage6_output=stage6_output,
                metadata=metadata or {},
            )

        pipeline_summary = self._build_context_summary(bound_context)

        # Dispatch to Multi-Agent Orchestrator
        orch_request = MultiAgentOrchestrationRequest(
            question=query,
            context=bound_context,
            retrieval_query=retrieval_query,
            max_evidence_items=max_evidence_items,
            enable_market=enable_market,
            enable_risk=enable_risk,
            enable_procurement=enable_procurement,
            metadata=metadata or {},
        )

        orch_response = self.orchestrator.orchestrate(orch_request)

        return FreightWiseAIServiceResponse(
            query=query,
            orchestration_response=orch_response,
            synthesized_answer=orch_response.synthesized_answer,
            status=orch_response.response_status,
            pipeline_context_summary=pipeline_summary,
            metadata=metadata or {},
        )
