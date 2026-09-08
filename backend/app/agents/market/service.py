"""Stage 7.4 Market Analyst Service Orchestrator."""

import copy
from typing import Any, Dict, List, Optional, Union

from app.agents.contracts import AgentContext, EvidenceItem, ProvenanceRecord
from app.agents.market.agent import BaseMarketAnalystModel, get_market_analyst_model
from app.agents.market.contracts import MarketAnalysisRequest, MarketAnalysisResponse, MarketFinding
from app.agents.safety import validate_agent_response, verify_authoritative_immutability
from app.rag.query import RetrievalQuery
from app.rag.retriever import RAGRetriever


class MarketAnalystService:
    """Service orchestrator for the Stage 7.4 Market Analyst Agent."""

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        model: Optional[BaseMarketAnalystModel] = None,
        is_testing: bool = False,
    ):
        self.is_testing = is_testing
        self.retriever = retriever or RAGRetriever(is_testing=is_testing)
        self.model = model or get_market_analyst_model(is_testing=is_testing)

    def _extract_numerical_inputs(self, context: AgentContext) -> Dict[str, Any]:
        """Extract authoritative Stage 2-6 numerical outputs into a clean summary dict."""
        summary: Dict[str, Any] = {}
        if context.freight_forecast:
            summary["freight_forecast"] = copy.deepcopy(context.freight_forecast)
        if context.delay_prediction:
            summary["delay_prediction"] = copy.deepcopy(context.delay_prediction)
        if context.congestion_prediction:
            summary["congestion_prediction"] = copy.deepcopy(context.congestion_prediction)
        if context.feasibility_result:
            summary["feasibility_result"] = copy.deepcopy(context.feasibility_result)
        if context.cost_result:
            summary["cost_result"] = copy.deepcopy(context.cost_result)
        if context.optimization_result:
            summary["optimization_result"] = copy.deepcopy(context.optimization_result)
        return summary

    def analyze(
        self,
        request: Union[MarketAnalysisRequest, str],
        context: Optional[AgentContext] = None,
    ) -> MarketAnalysisResponse:
        """Execute market analysis request downstream of Stage 2-6 numerical pipeline.

        Must NOT perform numerical calculations or mutate original context or evidence lists.
        """
        # 1. Parse and validate request
        if isinstance(request, str):
            req = MarketAnalysisRequest(question=request, context=context)
        elif isinstance(request, MarketAnalysisRequest):
            req = request
            req.validate()
        else:
            raise ValueError("Request must be a string or MarketAnalysisRequest object.")

        # 2. Context binding (deep copy to prevent caller context mutation)
        raw_ctx = req.context or context or AgentContext()
        ctx = copy.deepcopy(raw_ctx)

        # 3. Query Stage 7.3 RAG Retrieval Service
        retrieved_evidence: List[EvidenceItem] = []
        if req.question or req.retrieval_query:
            query_str = req.retrieval_query or req.question
            rag_res = self.retriever.retrieve(
                RetrievalQuery(query=query_str, top_k=req.max_evidence_items)
            )

            if rag_res and rag_res.results:
                for chunk in rag_res.results:
                    prov = ProvenanceRecord(
                        record_id=f"prov_rag_{chunk.chunk_id}",
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

        # Combine RAG evidence with existing context evidence
        all_evidence = list(ctx.evidence) + [
            e for e in retrieved_evidence if e.evidence_id not in {x.evidence_id for x in ctx.evidence}
        ]

        # 4. Generate response via LLM Model Provider
        agent_res = self.model.generate(request=req, context=ctx, evidence=all_evidence)

        # 5. Handle Provider Unavailable status
        if agent_res.status == "PROVIDER_UNAVAILABLE":
            return MarketAnalysisResponse(
                answer=agent_res.answer,
                key_findings=[],
                evidence=all_evidence,
                numerical_inputs=self._extract_numerical_inputs(ctx),
                limitations=agent_res.limitations or ["LLM provider unavailable."],
                warnings=["Provider unavailable."],
                provenance=agent_res.provenance,
                model_name=self.model.model_name,
                model_version=self.model.model_version,
                response_status="PROVIDER_UNAVAILABLE",
            )

        # 6. Safety & Immutability Verification (Stage 7.1 Rules)
        safety_res = validate_agent_response(agent_res, context=ctx)
        immutability_res = verify_authoritative_immutability(ctx, ctx)

        if not safety_res.is_valid or not immutability_res.is_valid:
            violations = safety_res.violations + immutability_res.violations
            return MarketAnalysisResponse(
                answer=agent_res.answer,
                key_findings=[],
                evidence=all_evidence,
                numerical_inputs=self._extract_numerical_inputs(ctx),
                limitations=["Safety validation failed: response contains forbidden claims or numerical overrides."],
                warnings=violations,
                provenance=agent_res.provenance,
                model_name=self.model.model_name,
                model_version=self.model.model_version,
                response_status="VALIDATION_FAILED",
            )

        # 7. Construct Key Findings & Link Valid Evidence IDs
        valid_ev_ids = {e.evidence_id for e in all_evidence}
        key_findings: List[MarketFinding] = []

        if ctx.freight_forecast:
            rate = ctx.freight_forecast.get("predicted_freight_rate") or ctx.freight_forecast.get("predicted_rate")
            if rate is not None:
                key_findings.append(
                    MarketFinding(
                        finding=f"Stage 2 freight forecast predicts rate of {rate} USD/day.",
                        basis="AUTHORITATIVE_PIPELINE",
                        evidence_ids=[],
                        numerical_reference=f"predicted_rate={rate}",
                        confidence_label="SUPPORTED",
                    )
                )

        for ev in retrieved_evidence:
            if ev.evidence_id in valid_ev_ids:
                key_findings.append(
                    MarketFinding(
                        finding=f"RAG document evidence chunk from '{ev.source}'.",
                        basis="RETRIEVED_EVIDENCE",
                        evidence_ids=[ev.evidence_id],
                        confidence_label="SUPPORTED",
                    )
                )

        limitations_list = list(agent_res.limitations) if agent_res.limitations else []
        if req.include_limitations and not limitations_list:
            limitations_list = [
                "Market Analyst Agent layer is explanatory only; does NOT make numerical decisions.",
                "GLOBAL_CONGESTION_PROXY is a global indicator and cannot be claimed as verified Indian port congestion."
            ]

        # 8. Return final MarketAnalysisResponse
        return MarketAnalysisResponse(
            answer=agent_res.answer,
            key_findings=key_findings,
            evidence=all_evidence,
            numerical_inputs=self._extract_numerical_inputs(ctx),
            limitations=limitations_list,
            warnings=safety_res.warnings,
            provenance=agent_res.provenance,
            model_name=self.model.model_name,
            model_version=self.model.model_version,
            response_status="SUCCESS",
        )
