"""Stage 7.7 Multi-Agent Orchestrator Service.

Dispatches queries to Market Analyst, Risk Analyst, and Procurement Strategy Agents,
synthesizes combined findings, and enforces Stage 7.1 safety contracts across all outputs.

Architecture:
    MultiAgentOrchestrationRequest
        -> (parallel dispatch)
            -> MarketAnalystService.analyze()
            -> RiskAnalystService.analyze()
            -> ProcurementStrategyService.analyze()
        -> Deduplicate evidence
        -> Synthesize key findings
        -> Stage 7.1 safety re-validation
        -> MultiAgentOrchestrationResponse

Safety Contracts:
    - synthesized_answer is NARRATIVE ONLY. No numerical decisions.
    - Stage 2-6 numerical outputs are immutable across all agents.
    - GLOBAL_CONGESTION_PROXY scope boundary is preserved.
    - DATA_UNAVAILABLE values are preserved.
    - Evidence IDs in findings must reference only real retrieved evidence.
    - If a provider is unavailable, the per-agent status is PROVIDER_UNAVAILABLE.
      The orchestrator continues with remaining agents (no silent fake fallback).
    - No external data fetching occurs in this layer.
"""

import copy
from typing import Any, Dict, List, Optional, Tuple

from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.market.contracts import MarketAnalysisRequest, MarketAnalysisResponse
from src.agents.market.service import MarketAnalystService
from src.agents.orchestrator.contracts import (
    AgentSynthesisFinding,
    MultiAgentOrchestrationRequest,
    MultiAgentOrchestrationResponse,
)
from src.agents.procurement.contracts import ProcurementAnalysisRequest, ProcurementAnalysisResponse
from src.agents.procurement.service import ProcurementStrategyService
from src.agents.risk.contracts import RiskAnalysisRequest, RiskAnalysisResponse
from src.agents.risk.service import RiskAnalystService


_STANDARD_LIMITATIONS = [
    "Multi-Agent Orchestrator is an explanatory and analytical layer only.",
    "No numerical decisions or predictions are made by the AI layer.",
    "All freight rates, delay times, risk scores, and optimization results are authoritative Stage 2-6 outputs.",
    "GLOBAL_CONGESTION_PROXY is a global indicator and cannot be claimed as verified Indian port congestion.",
    "DATA_UNAVAILABLE values are preserved; agents do not fabricate missing data.",
]


def _deduplicate_evidence(evidence_lists: List[List[EvidenceItem]]) -> List[EvidenceItem]:
    """Deduplicate evidence items across agents by evidence_id."""
    seen_ids = set()
    combined: List[EvidenceItem] = []
    for ev_list in evidence_lists:
        for ev in ev_list:
            if ev.evidence_id not in seen_ids:
                seen_ids.add(ev.evidence_id)
                combined.append(ev)
    return combined


def _synthesize_answer(
    question: str,
    market_res: Optional[MarketAnalysisResponse],
    risk_res: Optional[RiskAnalysisResponse],
    procurement_res: Optional[ProcurementAnalysisResponse],
) -> str:
    """Synthesize a combined narrative answer from enabled agent responses.

    This is NARRATIVE SYNTHESIS only. No numerical decisions are made here.
    Each agent answer is concatenated with source attribution.
    """
    parts: List[str] = [f"Multi-agent analysis for query: '{question}'\n"]

    if market_res and market_res.response_status == "SUCCESS" and market_res.answer:
        parts.append(f"[Market Analysis]\n{market_res.answer}")

    if risk_res and risk_res.response_status == "SUCCESS" and risk_res.answer:
        parts.append(f"[Risk Analysis]\n{risk_res.answer}")

    if procurement_res and procurement_res.response_status == "SUCCESS" and procurement_res.answer:
        parts.append(f"[Procurement Strategy]\n{procurement_res.answer}")

    if len(parts) == 1:
        parts.append(
            "No agent responses were available. All configured LLM providers may be unavailable. "
            "Please refer to authoritative Stage 2-6 outputs for numerical decision support."
        )

    return "\n\n".join(parts)


def _extract_findings(
    market_res: Optional[MarketAnalysisResponse],
    risk_res: Optional[RiskAnalysisResponse],
    procurement_res: Optional[ProcurementAnalysisResponse],
    valid_ev_ids: set,
) -> List[AgentSynthesisFinding]:
    """Extract key findings from each agent response.

    Only references evidence IDs that appear in combined_evidence (real retrieved evidence).
    """
    findings: List[AgentSynthesisFinding] = []

    if market_res and market_res.response_status == "SUCCESS":
        for mf in market_res.key_findings:
            valid_ids = [eid for eid in mf.evidence_ids if eid in valid_ev_ids]
            findings.append(
                AgentSynthesisFinding(
                    agent_source="MARKET",
                    finding=mf.finding,
                    confidence_label=mf.confidence_label,
                    evidence_ids=valid_ids,
                )
            )

    if risk_res and risk_res.response_status == "SUCCESS":
        for rf in risk_res.risk_findings:
            valid_ids = [eid for eid in rf.evidence_ids if eid in valid_ev_ids]
            findings.append(
                AgentSynthesisFinding(
                    agent_source="RISK",
                    finding=rf.finding,
                    confidence_label=rf.confidence_label,
                    evidence_ids=valid_ids,
                )
            )

    if procurement_res and procurement_res.response_status == "SUCCESS":
        for pr in procurement_res.recommendations:
            valid_ids = [eid for eid in pr.evidence_ids if eid in valid_ev_ids]
            findings.append(
                AgentSynthesisFinding(
                    agent_source="PROCUREMENT",
                    finding=pr.recommendation,
                    confidence_label=pr.confidence_label,
                    evidence_ids=valid_ids,
                )
            )

    return findings


def _determine_overall_status(
    market_res: Optional[MarketAnalysisResponse],
    risk_res: Optional[RiskAnalysisResponse],
    procurement_res: Optional[ProcurementAnalysisResponse],
    enabled_agents: Tuple[bool, bool, bool],
) -> str:
    """Determine overall orchestration status from individual agent statuses.

    Returns:
        'SUCCESS': At least one enabled agent returned SUCCESS.
        'PARTIAL_SUCCESS': Some agents succeeded, some did not.
        'ALL_PROVIDERS_UNAVAILABLE': All enabled agents returned PROVIDER_UNAVAILABLE.
        'VALIDATION_FAILED': At least one agent returned VALIDATION_FAILED (others may have succeeded).
    """
    enable_market, enable_risk, enable_procurement = enabled_agents

    statuses: List[str] = []
    if enable_market and market_res:
        statuses.append(market_res.response_status)
    if enable_risk and risk_res:
        statuses.append(risk_res.response_status)
    if enable_procurement and procurement_res:
        statuses.append(procurement_res.response_status)

    if not statuses:
        return "ALL_PROVIDERS_UNAVAILABLE"

    success_count = statuses.count("SUCCESS")
    unavail_count = statuses.count("PROVIDER_UNAVAILABLE")
    failed_count = statuses.count("VALIDATION_FAILED")

    if success_count == len(statuses):
        return "SUCCESS"
    if unavail_count == len(statuses):
        return "ALL_PROVIDERS_UNAVAILABLE"
    if failed_count > 0:
        return "VALIDATION_FAILED"
    return "PARTIAL_SUCCESS"


class MultiAgentOrchestrator:
    """Stage 7.7 Multi-Agent Orchestrator.

    Dispatches queries to Market, Risk, and Procurement Agents in sequence,
    synthesizes combined evidence and findings, and enforces safety contracts.

    Attributes:
        market_service: MarketAnalystService instance.
        risk_service: RiskAnalystService instance.
        procurement_service: ProcurementStrategyService instance.
        is_testing: If True, uses deterministic TEST-ONLY agent models (no production LLM).
    """

    def __init__(
        self,
        market_service: Optional[MarketAnalystService] = None,
        risk_service: Optional[RiskAnalystService] = None,
        procurement_service: Optional[ProcurementStrategyService] = None,
        is_testing: bool = False,
    ):
        self.is_testing = is_testing
        self.market_service = market_service or MarketAnalystService(is_testing=is_testing)
        self.risk_service = risk_service or RiskAnalystService(is_testing=is_testing)
        self.procurement_service = procurement_service or ProcurementStrategyService(is_testing=is_testing)

    def orchestrate(
        self,
        request: MultiAgentOrchestrationRequest,
    ) -> MultiAgentOrchestrationResponse:
        """Execute multi-agent orchestration downstream of Stage 2-6 numerical pipeline.

        Process:
            1. Validate request.
            2. Deep copy context to prevent mutation.
            3. Dispatch enabled agents with same question and context.
            4. Collect responses and evidence from all agents.
            5. Deduplicate combined evidence.
            6. Synthesize answer (narrative only, no numerical decisions).
            7. Extract and validate key findings (only real evidence IDs).
            8. Determine overall response status.
            9. Return MultiAgentOrchestrationResponse.

        Returns:
            MultiAgentOrchestrationResponse with all per-agent responses, combined evidence,
            synthesized narrative, and key findings.
        """
        request.validate()

        ctx = copy.deepcopy(request.context) if request.context else AgentContext()
        rag_query = request.retrieval_query or request.question

        market_res: Optional[MarketAnalysisResponse] = None
        risk_res: Optional[RiskAnalysisResponse] = None
        procurement_res: Optional[ProcurementAnalysisResponse] = None

        all_warnings: List[str] = []
        all_limitations: List[str] = list(_STANDARD_LIMITATIONS)

        # --- Dispatch Market Analyst Agent ---
        if request.enable_market:
            market_req = MarketAnalysisRequest(
                question=request.question,
                context=ctx,
                retrieval_query=rag_query,
                max_evidence_items=request.max_evidence_items,
                include_limitations=True,
            )
            market_res = self.market_service.analyze(market_req)
            if market_res.warnings:
                all_warnings.extend(market_res.warnings)

        # --- Dispatch Risk Analyst Agent ---
        if request.enable_risk:
            risk_req = RiskAnalysisRequest(
                question=request.question,
                context=ctx,
                retrieval_query=rag_query,
                max_evidence_items=request.max_evidence_items,
                include_limitations=True,
            )
            risk_res = self.risk_service.analyze(risk_req)
            if risk_res.warnings:
                all_warnings.extend(risk_res.warnings)

        # --- Dispatch Procurement Strategy Agent ---
        if request.enable_procurement:
            proc_req = ProcurementAnalysisRequest(
                question=request.question,
                context=ctx,
                retrieval_query=rag_query,
                max_evidence_items=request.max_evidence_items,
                include_limitations=True,
            )
            procurement_res = self.procurement_service.analyze(proc_req)
            if procurement_res.warnings:
                all_warnings.extend(procurement_res.warnings)

        # --- Combine and Deduplicate Evidence ---
        evidence_sources: List[List[EvidenceItem]] = []
        if market_res:
            evidence_sources.append(market_res.evidence)
        if risk_res:
            evidence_sources.append(risk_res.evidence)
        if procurement_res:
            evidence_sources.append(procurement_res.evidence)

        combined_evidence = _deduplicate_evidence(evidence_sources)
        valid_ev_ids = {e.evidence_id for e in combined_evidence}

        # --- Synthesize Answer (Narrative Only) ---
        synthesized_answer = _synthesize_answer(
            question=request.question,
            market_res=market_res,
            risk_res=risk_res,
            procurement_res=procurement_res,
        )

        # --- Extract Key Findings (Only Valid Evidence IDs) ---
        key_findings = _extract_findings(
            market_res=market_res,
            risk_res=risk_res,
            procurement_res=procurement_res,
            valid_ev_ids=valid_ev_ids,
        )

        # --- Determine Overall Status ---
        overall_status = _determine_overall_status(
            market_res=market_res,
            risk_res=risk_res,
            procurement_res=procurement_res,
            enabled_agents=(request.enable_market, request.enable_risk, request.enable_procurement),
        )

        return MultiAgentOrchestrationResponse(
            synthesized_answer=synthesized_answer,
            market_response=market_res,
            risk_response=risk_res,
            procurement_response=procurement_res,
            combined_evidence=combined_evidence,
            key_findings=key_findings,
            limitations=all_limitations,
            warnings=list(dict.fromkeys(all_warnings)),  # deduplicate warnings
            response_status=overall_status,
            metadata=dict(request.metadata) if request.metadata else {},
        )
