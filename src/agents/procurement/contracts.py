"""Stage 7.6 Data Contracts for Procurement Agent Layer."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional

from src.agents.contracts import AgentContext, EvidenceItem, ProvenanceRecord
from src.agents.market.contracts import VALID_CONFIDENCE_LABELS


def _generate_uuid() -> str:
    return f"req_proc_{uuid.uuid4().hex[:12]}"


@dataclass
class ProcurementAnalysisRequest:
    """Input request contract for the Procurement Strategy Agent."""

    question: str
    context: Optional[AgentContext] = None
    retrieval_query: Optional[str] = None
    max_evidence_items: int = 5
    include_limitations: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("ProcurementAnalysisRequest question cannot be empty or whitespace-only.")
        if not isinstance(self.max_evidence_items, int) or self.max_evidence_items <= 0:
            raise ValueError("max_evidence_items must be a positive integer.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "context": self.context.to_dict() if self.context else None,
            "retrieval_query": self.retrieval_query,
            "max_evidence_items": self.max_evidence_items,
            "include_limitations": self.include_limitations,
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcurementAnalysisRequest":
        ctx_raw = data.get("context")
        ctx = AgentContext.from_dict(ctx_raw) if ctx_raw else None
        return cls(
            question=data.get("question", ""),
            context=ctx,
            retrieval_query=data.get("retrieval_query"),
            max_evidence_items=data.get("max_evidence_items", 5),
            include_limitations=data.get("include_limitations", True),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ProcurementAnalysisRequest":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ProcurementRecommendation:
    """Strategy recommendation explaining pre-computed Stage 5/6 optimization choices."""

    recommendation: str
    strategy_category: str  # 'CHARTER_STRATEGY', 'OPTIMIZER_PLAN_EXPLANATION', 'SCENARIO_COMPARISON'
    evidence_ids: List[str] = field(default_factory=list)
    numerical_reference: Optional[str] = None
    confidence_label: str = "SUPPORTED"

    def __post_init__(self):
        if self.confidence_label not in VALID_CONFIDENCE_LABELS:
            raise ValueError(
                f"Invalid confidence_label '{self.confidence_label}'. Must be one of: {sorted(list(VALID_CONFIDENCE_LABELS))}."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "strategy_category": self.strategy_category,
            "evidence_ids": list(self.evidence_ids),
            "numerical_reference": self.numerical_reference,
            "confidence_label": self.confidence_label,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcurementRecommendation":
        return cls(
            recommendation=data.get("recommendation", ""),
            strategy_category=data.get("strategy_category", "CHARTER_STRATEGY"),
            evidence_ids=list(data.get("evidence_ids", [])),
            numerical_reference=data.get("numerical_reference"),
            confidence_label=data.get("confidence_label", "SUPPORTED"),
        )


@dataclass
class ProcurementAnalysisResponse:
    """Structured procurement strategy response payload."""

    request_id: str = field(default_factory=_generate_uuid)
    answer: str = ""
    recommendations: List[ProcurementRecommendation] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    numerical_inputs: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    provenance: Optional[ProvenanceRecord] = None
    model_name: str = "UNASSIGNED"
    model_version: str = "1.0.0"
    response_status: str = "SUCCESS"  # 'SUCCESS', 'VALIDATION_FAILED', 'PROVIDER_UNAVAILABLE'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "answer": self.answer,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "evidence": [e.to_dict() for e in self.evidence],
            "numerical_inputs": dict(self.numerical_inputs) if self.numerical_inputs else {},
            "limitations": list(self.limitations),
            "warnings": list(self.warnings),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "response_status": self.response_status,
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcurementAnalysisResponse":
        recs_raw = data.get("recommendations", [])
        recs = [ProcurementRecommendation.from_dict(r) if isinstance(r, dict) else r for r in recs_raw]

        evidence_raw = data.get("evidence", [])
        evidence_items = [EvidenceItem.from_dict(e) if isinstance(e, dict) else e for e in evidence_raw]

        prov_raw = data.get("provenance")
        prov = ProvenanceRecord.from_dict(prov_raw) if prov_raw else None

        return cls(
            request_id=data.get("request_id") or _generate_uuid(),
            answer=data.get("answer", ""),
            recommendations=recs,
            evidence=evidence_items,
            numerical_inputs=dict(data.get("numerical_inputs", {})),
            limitations=list(data.get("limitations", [])),
            warnings=list(data.get("warnings", [])),
            provenance=prov,
            model_name=data.get("model_name", "UNASSIGNED"),
            model_version=data.get("model_version", "1.0.0"),
            response_status=data.get("response_status", "SUCCESS"),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ProcurementAnalysisResponse":
        return cls.from_dict(json.loads(json_str))
