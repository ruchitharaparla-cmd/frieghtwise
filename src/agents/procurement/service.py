"""Stage 7.6 Procurement Strategy Service Orchestrator."""

import copy
from typing import Any, Dict, List, Optional, Union

from src.agents.contracts import AgentContext, EvidenceItem, ProvenanceRecord
from src.agents.procurement.agent import BaseProcurementModel, get_procurement_model
from src.agents.procurement.contracts import ProcurementAnalysisRequest, ProcurementAnalysisResponse, ProcurementRecommendation
from src.agents.safety import validate_agent_response, verify_authoritative_immutability
from src.rag.query import RetrievalQuery
from src.rag.retriever import RAGRetriever


class ProcurementStrategyService:
    """Service orchestrator for the Stage 7.6 Procurement Strategy Agent."""

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        model: Optional[BaseProcurementModel] = None,
        is_testing: bool = False,
    ):
        self.is_testing = is_testing
        self.retriever = retriever or RAGRetriever(is_testing=is_testing)
        self.model = model or get_procurement_model(is_testing=is_testing)

    def _extract_numerical_inputs(self, context: AgentContext) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        if context.freight_forecast:
            summary["freight_forecast"] = copy.deepcopy(context.freight_forecast)
        if context.cost_result:
            summary["cost_result"] = copy.deepcopy(context.cost_result)
        if context.optimization_result:
            summary["optimization_result"] = copy.deepcopy(context.optimization_result)
        return summary

    def analyze(
        self,
        request: Union[ProcurementAnalysisRequest, str],
        context: Optional[AgentContext] = None,
    ) -> ProcurementAnalysisResponse:
        if isinstance(request, str):
            req = ProcurementAnalysisRequest(question=request, context=context)
        elif isinstance(request, ProcurementAnalysisRequest):
            req = request
            req.validate()
        else:
            raise ValueError("Request must be a string or ProcurementAnalysisRequest object.")

        raw_ctx = req.context or context or AgentContext()
        ctx = copy.deepcopy(raw_ctx)

        retrieved_evidence: List[EvidenceItem] = []
        if req.question or req.retrieval_query:
            q_str = req.retrieval_query or req.question
            rag_res = self.retriever.retrieve(RetrievalQuery(query=q_str, top_k=req.max_evidence_items))
            if rag_res and rag_res.results:
                for chunk in rag_res.results:
                    prov = ProvenanceRecord(
                        record_id=f"prov_proc_rag_{chunk.chunk_id}",
                        source=chunk.metadata.get("filename", chunk.document_id),
                        source_type="DOCUMENT",
                        stage=chunk.metadata.get("stage", "Stage 7.3"),
                        document_name=chunk.metadata.get("filename"),
                        data_scope=chunk.metadata.get("source", "AUTHORIZED"),
                        metadata=dict(chunk.metadata),
                    )
                    ev_item = EvidenceItem(
                        evidence_id=chunk.chunk_id,
                        content=chunk.text,
                        source=chunk.metadata.get("filename", chunk.document_id),
                        source_type="DOCUMENT",
                        relevance=chunk.relevance,
                        metadata=dict(chunk.metadata),
                        provenance=prov,
                    )
                    retrieved_evidence.append(ev_item)

        all_evidence = list(ctx.evidence) + [
            e for e in retrieved_evidence if e.evidence_id not in {x.evidence_id for x in ctx.evidence}
        ]

        agent_res = self.model.generate(request=req, context=ctx, evidence=all_evidence)

        if agent_res.status == "PROVIDER_UNAVAILABLE":
            return ProcurementAnalysisResponse(
                answer=agent_res.answer,
                recommendations=[],
                evidence=all_evidence,
                numerical_inputs=self._extract_numerical_inputs(ctx),
                limitations=agent_res.limitations or ["Procurement LLM provider unavailable."],
                warnings=["Provider unavailable."],
                provenance=agent_res.provenance,
                model_name=self.model.model_name,
                model_version=self.model.model_version,
                response_status="PROVIDER_UNAVAILABLE",
            )

        safety_res = validate_agent_response(agent_res, context=ctx)
        immutability_res = verify_authoritative_immutability(ctx, ctx)

        if not safety_res.is_valid or not immutability_res.is_valid:
            violations = safety_res.violations + immutability_res.violations
            return ProcurementAnalysisResponse(
                answer=agent_res.answer,
                recommendations=[],
                evidence=all_evidence,
                numerical_inputs=self._extract_numerical_inputs(ctx),
                limitations=["Safety validation failed: response contains forbidden claims or numerical overrides."],
                warnings=violations,
                provenance=agent_res.provenance,
                model_name=self.model.model_name,
                model_version=self.model.model_version,
                response_status="VALIDATION_FAILED",
            )

        valid_ev_ids = {e.evidence_id for e in all_evidence}
        recommendations: List[ProcurementRecommendation] = []

        if ctx.optimization_result:
            vessel = ctx.optimization_result.get("selected_vessel_id") or ctx.optimization_result.get("optimal_schedule")
            if vessel:
                recommendations.append(
                    ProcurementRecommendation(
                        recommendation=f"Execute allocation plan selected by Stage 6 optimizer for {vessel}.",
                        strategy_category="OPTIMIZER_PLAN_EXPLANATION",
                        evidence_ids=[],
                        numerical_reference=f"selected_vessel_id={vessel}",
                        confidence_label="SUPPORTED",
                    )
                )

        for ev in retrieved_evidence:
            if ev.evidence_id in valid_ev_ids:
                recommendations.append(
                    ProcurementRecommendation(
                        recommendation=f"Procurement strategy evidence from '{ev.source}'.",
                        strategy_category="CHARTER_STRATEGY",
                        evidence_ids=[ev.evidence_id],
                        confidence_label="SUPPORTED",
                    )
                )

        limitations_list = list(agent_res.limitations) if agent_res.limitations else []
        if req.include_limitations and not limitations_list:
            limitations_list = [
                "Procurement Agent layer is explanatory only; does NOT override Stage 6 CP-SAT solver selections.",
                "Voyage charter costs are computed by Stage 5 cost engine and cannot be altered."
            ]

        return ProcurementAnalysisResponse(
            answer=agent_res.answer,
            recommendations=recommendations,
            evidence=all_evidence,
            numerical_inputs=self._extract_numerical_inputs(ctx),
            limitations=limitations_list,
            warnings=safety_res.warnings,
            provenance=agent_res.provenance,
            model_name=self.model.model_name,
            model_version=self.model.model_version,
            response_status="SUCCESS",
        )
