"""Stage 7.7 Data Contracts for Multi-Agent Orchestrator.

Defines request/response schemas for multi-agent orchestration combining
Market Analyst, Risk Analyst, and Procurement Strategy Agents.

Safety Rules:
- Combined responses must NEVER mutate Stage 2-6 numerical outputs.
- Evidence IDs in synthesized findings must reference only real retrieved evidence.
- DATA_UNAVAILABLE and GLOBAL_CONGESTION_PROXY are preserved across all agents.
- If any agent returns PROVIDER_UNAVAILABLE or VALIDATION_FAILED, that status is
  reflected per-agent in the combined response. The orchestrator continues with
  remaining agents and does NOT fail the entire request.
"""

from dataclasses import dataclass, field
import json
import uuid
from typing import Any, Dict, List, Optional

from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.market.contracts import MarketAnalysisResponse
from src.agents.risk.contracts import RiskAnalysisResponse
from src.agents.procurement.contracts import ProcurementAnalysisResponse


def _generate_orch_uuid() -> str:
    return f"req_orch_{uuid.uuid4().hex[:12]}"


@dataclass
class MultiAgentOrchestrationRequest:
    """Input request contract for the Multi-Agent Orchestrator.

    Fields:
        question: User question or analytical query.
        context: Authoritative Stage 2-6 pipeline context.
        retrieval_query: Optional override for RAG retrieval query. Defaults to question.
        max_evidence_items: Maximum evidence items per agent retrieval call.
        enable_market: Whether to invoke the Market Analyst Agent.
        enable_risk: Whether to invoke the Risk Analyst Agent.
        enable_procurement: Whether to invoke the Procurement Strategy Agent.
        metadata: Extra key-value metadata.
    """

    question: str
    context: Optional[AgentContext] = None
    retrieval_query: Optional[str] = None
    max_evidence_items: int = 5
    enable_market: bool = True
    enable_risk: bool = True
    enable_procurement: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("MultiAgentOrchestrationRequest question cannot be empty or whitespace-only.")
        if not isinstance(self.max_evidence_items, int) or self.max_evidence_items <= 0:
            raise ValueError("max_evidence_items must be a positive integer.")
        if not any([self.enable_market, self.enable_risk, self.enable_procurement]):
            raise ValueError("At least one agent must be enabled.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "context": self.context.to_dict() if self.context else None,
            "retrieval_query": self.retrieval_query,
            "max_evidence_items": self.max_evidence_items,
            "enable_market": self.enable_market,
            "enable_risk": self.enable_risk,
            "enable_procurement": self.enable_procurement,
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiAgentOrchestrationRequest":
        ctx_raw = data.get("context")
        ctx = AgentContext.from_dict(ctx_raw) if ctx_raw else None
        return cls(
            question=data.get("question", ""),
            context=ctx,
            retrieval_query=data.get("retrieval_query"),
            max_evidence_items=data.get("max_evidence_items", 5),
            enable_market=data.get("enable_market", True),
            enable_risk=data.get("enable_risk", True),
            enable_procurement=data.get("enable_procurement", True),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "MultiAgentOrchestrationRequest":
        return cls.from_dict(json.loads(json_str))


@dataclass
class AgentSynthesisFinding:
    """A single synthesized finding extracted from a specific agent's response.

    Fields:
        agent_source: Which agent produced this finding ('MARKET', 'RISK', 'PROCUREMENT').
        finding: The synthesized finding or observation.
        confidence_label: 'SUPPORTED', 'PARTIALLY_SUPPORTED', or 'DATA_LIMITED'.
        evidence_ids: Evidence IDs supporting this finding (must reference real retrieved evidence).
    """

    agent_source: str  # 'MARKET', 'RISK', 'PROCUREMENT'
    finding: str
    confidence_label: str = "SUPPORTED"
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_source": self.agent_source,
            "finding": self.finding,
            "confidence_label": self.confidence_label,
            "evidence_ids": list(self.evidence_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSynthesisFinding":
        return cls(
            agent_source=data.get("agent_source", "UNKNOWN"),
            finding=data.get("finding", ""),
            confidence_label=data.get("confidence_label", "SUPPORTED"),
            evidence_ids=list(data.get("evidence_ids", [])),
        )


@dataclass
class MultiAgentOrchestrationResponse:
    """Structured multi-agent orchestration response.

    Combines Market, Risk, and Procurement Agent outputs into a unified response.
    All individual agent responses are preserved for traceability.

    Safety contract:
        - synthesized_answer is a narrative synthesis ONLY; no numerical decisions.
        - combined_evidence contains deduplicated real evidence from all agent calls.
        - key_findings are extracted from individual agent responses.
        - Immutability of Stage 2-6 numerical outputs is enforced across all sub-agents.
    """

    request_id: str = field(default_factory=_generate_orch_uuid)
    synthesized_answer: str = ""
    market_response: Optional[MarketAnalysisResponse] = None
    risk_response: Optional[RiskAnalysisResponse] = None
    procurement_response: Optional[ProcurementAnalysisResponse] = None
    combined_evidence: List[EvidenceItem] = field(default_factory=list)
    key_findings: List[AgentSynthesisFinding] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    response_status: str = "SUCCESS"
    # 'SUCCESS', 'PARTIAL_SUCCESS', 'ALL_PROVIDERS_UNAVAILABLE', 'VALIDATION_FAILED'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "synthesized_answer": self.synthesized_answer,
            "market_response": self.market_response.to_dict() if self.market_response else None,
            "risk_response": self.risk_response.to_dict() if self.risk_response else None,
            "procurement_response": self.procurement_response.to_dict() if self.procurement_response else None,
            "combined_evidence": [e.to_dict() for e in self.combined_evidence],
            "key_findings": [f.to_dict() for f in self.key_findings],
            "limitations": list(self.limitations),
            "warnings": list(self.warnings),
            "response_status": self.response_status,
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiAgentOrchestrationResponse":
        market_raw = data.get("market_response")
        market = MarketAnalysisResponse.from_dict(market_raw) if market_raw else None

        risk_raw = data.get("risk_response")
        risk = RiskAnalysisResponse.from_dict(risk_raw) if risk_raw else None

        proc_raw = data.get("procurement_response")
        procurement = ProcurementAnalysisResponse.from_dict(proc_raw) if proc_raw else None

        evidence_raw = data.get("combined_evidence", [])
        combined_evidence = [EvidenceItem.from_dict(e) if isinstance(e, dict) else e for e in evidence_raw]

        findings_raw = data.get("key_findings", [])
        findings = [AgentSynthesisFinding.from_dict(f) if isinstance(f, dict) else f for f in findings_raw]

        return cls(
            request_id=data.get("request_id") or _generate_orch_uuid(),
            synthesized_answer=data.get("synthesized_answer", ""),
            market_response=market,
            risk_response=risk,
            procurement_response=procurement,
            combined_evidence=combined_evidence,
            key_findings=findings,
            limitations=list(data.get("limitations", [])),
            warnings=list(data.get("warnings", [])),
            response_status=data.get("response_status", "SUCCESS"),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "MultiAgentOrchestrationResponse":
        return cls.from_dict(json.loads(json_str))
