"""Stage 7.5 Risk Analyst Service Orchestrator."""

import copy
from typing import Any, Dict, List, Optional, Union

from src.agents.contracts import AgentContext, EvidenceItem, ProvenanceRecord
from src.agents.risk.agent import BaseRiskAnalystModel, get_risk_analyst_model
from src.agents.risk.contracts import RiskAnalysisRequest, RiskAnalysisResponse, RiskFinding
from src.agents.safety import validate_agent_response, verify_authoritative_immutability
from src.rag.query import RetrievalQuery
from src.rag.retriever import RAGRetriever


class RiskAnalystService:
    """Service orchestrator for the Stage 7.5 Risk Analyst Agent."""

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        model: Optional[BaseRiskAnalystModel] = None,
        is_testing: bool = False,
    ):
        self.is_testing = is_testing
        self.retriever = retriever or RAGRetriever(is_testing=is_testing)
        self.model = model or get_risk_analyst_model(is_testing=is_testing)

    def _extract_numerical_inputs(self, context: AgentContext) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        if context.delay_prediction:
            summary["delay_prediction"] = copy.deepcopy(context.delay_prediction)
        if context.congestion_prediction:
            summary["congestion_prediction"] = copy.deepcopy(context.congestion_prediction)
        if context.feasibility_result:
            summary["feasibility_result"] = copy.deepcopy(context.feasibility_result)
        if context.cost_result:
            summary["cost_result"] = copy.deepcopy(context.cost_result)
        return summary

    def analyze(
        self,
        request: Union[RiskAnalysisRequest, str],
        context: Optional[AgentContext] = None,
    ) -> RiskAnalysisResponse:
        if isinstance(request, str):
            req = RiskAnalysisRequest(question=request, context=context)
        elif isinstance(request, RiskAnalysisRequest):
            req = request
            req.validate()
        else:
            raise ValueError("Request must be a string or RiskAnalysisRequest object.")

        raw_ctx = req.context or context or AgentContext()
        ctx = copy.deepcopy(raw_ctx)

        retrieved_evidence: List[EvidenceItem] = []
        if req.question or req.retrieval_query:
            q_str = req.retrieval_query or req.question
            rag_res = self.retriever.retrieve(RetrievalQuery(query=q_str, top_k=req.max_evidence_items))
            if rag_res and rag_res.results:
                for chunk in rag_res.results:
                    prov = ProvenanceRecord(
                        record_id=f"prov_risk_rag_{chunk.chunk_id}",
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
            return RiskAnalysisResponse(
                answer=agent_res.answer,
                risk_findings=[],
                evidence=all_evidence,
                numerical_inputs=self._extract_numerical_inputs(ctx),
                limitations=agent_res.limitations or ["Risk LLM provider unavailable."],
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
            return RiskAnalysisResponse(
                answer=agent_res.answer,
                risk_findings=[],
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
        risk_findings: List[RiskFinding] = []

        if ctx.delay_prediction:
            hrs = ctx.delay_prediction.get("predicted_delay_hours") or ctx.delay_prediction.get("delay_hours")
            if hrs is not None:
                risk_findings.append(
                    RiskFinding(
                        finding=f"Stage 3 predicts turnaround delay of {hrs} hours.",
                        risk_category="TURNAROUND_DELAY",
                        evidence_ids=[],
                        numerical_reference=f"delay_hours={hrs}",
                        confidence_label="SUPPORTED",
                    )
                )

        for ev in retrieved_evidence:
            if ev.evidence_id in valid_ev_ids:
                risk_findings.append(
                    RiskFinding(
                        finding=f"Risk evidence from '{ev.source}'.",
                        risk_category="PORT_CONGESTION",
                        evidence_ids=[ev.evidence_id],
                        confidence_label="SUPPORTED",
                    )
                )

        limitations_list = list(agent_res.limitations) if agent_res.limitations else []
        if req.include_limitations and not limitations_list:
            limitations_list = [
                "Risk Agent is an explanatory layer; does NOT recalculate risk scores.",
                "GLOBAL_CONGESTION_PROXY is a global proxy and cannot be claimed as verified Indian port congestion."
            ]

        return RiskAnalysisResponse(
            answer=agent_res.answer,
            risk_findings=risk_findings,
            evidence=all_evidence,
            numerical_inputs=self._extract_numerical_inputs(ctx),
            limitations=limitations_list,
            warnings=safety_res.warnings,
            provenance=agent_res.provenance,
            model_name=self.model.model_name,
            model_version=self.model.model_version,
            response_status="SUCCESS",
        )
