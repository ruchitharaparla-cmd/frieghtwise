"""
Data contracts and serializable schemas for FreightWise Stage 7 AI Agents + RAG layer.

Defines strict typed contracts for EvidenceItem, AgentContext, AgentRequest,
AgentResponse, and ProvenanceRecord.

Strict Rule:
LLMs must NEVER make numerical decisions. All numerical data comes from Stage 1-6 outputs.
Missing values must remain None and have explicit unavailable statuses where applicable.
No default numerical values may be fabricated.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Union


def _current_timestamp_iso() -> str:
    """Helper to get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProvenanceRecord:
    """
    Metadata record establishing lineage and origin of evidence or agent context items.

    Fields:
        record_id: Unique record identifier.
        source: System component or module generating data (e.g., 'Stage2ForecastAdapter').
        source_type: Type of source ('MODEL', 'RULE_ENGINE', 'OPTIMIZER', 'DOCUMENT').
        stage: Pipeline stage name (e.g., 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5', 'Stage 6').
        model_name: ML model name if applicable.
        model_version: ML model version if applicable.
        document_name: Document identifier or title if RAG evidence.
        data_scope: Scope of data ('GLOBAL_CONGESTION_PROXY', 'EAST_COAST_INDIA', 'AUTHORIZED').
        timestamp: ISO UTC creation timestamp.
        metadata: Key-value dictionary for extra lineage attributes.
    """
    record_id: str
    source: str
    source_type: str
    stage: str
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    document_name: Optional[str] = None
    data_scope: str = "AUTHORIZED"
    timestamp: str = field(default_factory=_current_timestamp_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ProvenanceRecord to dictionary."""
        return {
            "record_id": self.record_id,
            "source": self.source,
            "source_type": self.source_type,
            "stage": self.stage,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "document_name": self.document_name,
            "data_scope": self.data_scope,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvenanceRecord":
        """Deserialize ProvenanceRecord from dictionary."""
        return cls(
            record_id=data.get("record_id", ""),
            source=data.get("source", ""),
            source_type=data.get("source_type", ""),
            stage=data.get("stage", ""),
            model_name=data.get("model_name"),
            model_version=data.get("model_version"),
            document_name=data.get("document_name"),
            data_scope=data.get("data_scope", "AUTHORIZED"),
            timestamp=data.get("timestamp") or _current_timestamp_iso(),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        """Serialize ProvenanceRecord to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ProvenanceRecord":
        """Deserialize ProvenanceRecord from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class EvidenceItem:
    """
    Retrieved evidence item supporting RAG retrieval or agent reasoning.

    Fields:
        evidence_id: Unique evidence identifier.
        content: Textual content or string representation of evidence.
        source: Source module, dataset, or document path.
        source_type: Category of source ('FORECAST', 'DELAY', 'CONGESTION', 'FEASIBILITY', 'COST', 'OPTIMIZATION', 'DOCUMENT').
        relevance: Relevance score between 0.0 and 1.0.
        metadata: Extra metadata dictionary.
        provenance: Optional linked ProvenanceRecord.
    """
    evidence_id: str
    content: str
    source: str
    source_type: str
    relevance: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance: Optional[ProvenanceRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize EvidenceItem to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "content": self.content,
            "source": self.source,
            "source_type": self.source_type,
            "relevance": self.relevance,
            "metadata": dict(self.metadata) if self.metadata else {},
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceItem":
        """Deserialize EvidenceItem from dictionary."""
        prov_data = data.get("provenance")
        prov = ProvenanceRecord.from_dict(prov_data) if prov_data else None
        return cls(
            evidence_id=data.get("evidence_id", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            source_type=data.get("source_type", ""),
            relevance=float(data.get("relevance", 1.0)),
            metadata=dict(data.get("metadata", {})),
            provenance=prov,
        )

    def to_json(self) -> str:
        """Serialize EvidenceItem to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "EvidenceItem":
        """Deserialize EvidenceItem from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class AgentContext:
    """
    Container for authoritative Stage 2-6 pipeline outputs and retrieved evidence.

    Explicitly preserves None for missing values. Does not fabricate numerical defaults.
    """
    freight_forecast: Optional[Dict[str, Any]] = None
    delay_prediction: Optional[Dict[str, Any]] = None
    congestion_prediction: Optional[Dict[str, Any]] = None
    feasibility_result: Optional[Dict[str, Any]] = None
    cost_result: Optional[Dict[str, Any]] = None
    optimization_result: Optional[Dict[str, Any]] = None
    evidence: List[EvidenceItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AgentContext to dictionary."""
        return {
            "freight_forecast": dict(self.freight_forecast) if self.freight_forecast is not None else None,
            "delay_prediction": dict(self.delay_prediction) if self.delay_prediction is not None else None,
            "congestion_prediction": dict(self.congestion_prediction) if self.congestion_prediction is not None else None,
            "feasibility_result": dict(self.feasibility_result) if self.feasibility_result is not None else None,
            "cost_result": dict(self.cost_result) if self.cost_result is not None else None,
            "optimization_result": dict(self.optimization_result) if self.optimization_result is not None else None,
            "evidence": [e.to_dict() for e in self.evidence],
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentContext":
        """Deserialize AgentContext from dictionary."""
        evidence_raw = data.get("evidence", [])
        evidence_items = [
            EvidenceItem.from_dict(item) if isinstance(item, dict) else item
            for item in evidence_raw
        ]
        return cls(
            freight_forecast=data.get("freight_forecast"),
            delay_prediction=data.get("delay_prediction"),
            congestion_prediction=data.get("congestion_prediction"),
            feasibility_result=data.get("feasibility_result"),
            cost_result=data.get("cost_result"),
            optimization_result=data.get("optimization_result"),
            evidence=evidence_items,
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        """Serialize AgentContext to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentContext":
        """Deserialize AgentContext from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class AgentRequest:
    """
    Input request contract sent to a Stage 7 AI Agent.

    Fields:
        agent_name: Target agent identifier.
        question: User or system prompt/query.
        context: Bound AgentContext containing authoritative Stage 2-6 pipeline data.
        retrieved_evidence: Additional retrieved evidence items.
        metadata: Extra query metadata.
    """
    agent_name: str
    question: str
    context: Optional[AgentContext] = None
    retrieved_evidence: List[EvidenceItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AgentRequest to dictionary."""
        return {
            "agent_name": self.agent_name,
            "question": self.question,
            "context": self.context.to_dict() if self.context else None,
            "retrieved_evidence": [e.to_dict() for e in self.retrieved_evidence],
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRequest":
        """Deserialize AgentRequest from dictionary."""
        ctx_data = data.get("context")
        ctx = AgentContext.from_dict(ctx_data) if ctx_data else None
        evidence_raw = data.get("retrieved_evidence", [])
        evidence_items = [
            EvidenceItem.from_dict(e) if isinstance(e, dict) else e
            for e in evidence_raw
        ]
        return cls(
            agent_name=data.get("agent_name", ""),
            question=data.get("question", ""),
            context=ctx,
            retrieved_evidence=evidence_items,
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        """Serialize AgentRequest to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentRequest":
        """Deserialize AgentRequest from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class AgentResponse:
    """
    Output response contract from a Stage 7 AI Agent.

    Fields:
        answer: Textual answer or explanation generated by the agent.
        evidence: List of EvidenceItems used to generate the answer.
        limitations: Explicit list of disclaimers, data gaps, or boundary notices.
        provenance: Optional ProvenanceRecord for the response generation.
        status: Execution status ('SUCCESS', 'VALIDATION_FAILED', 'INSUFFICIENT_EVIDENCE').
        confidence: Confidence level ('HIGH', 'MEDIUM', 'LOW').
        metadata: Extra metadata.
    """
    answer: str
    evidence: List[EvidenceItem] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    provenance: Optional[ProvenanceRecord] = None
    status: str = "SUCCESS"
    confidence: str = "HIGH"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AgentResponse to dictionary."""
        return {
            "answer": self.answer,
            "evidence": [e.to_dict() for e in self.evidence],
            "limitations": list(self.limitations),
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "status": self.status,
            "confidence": self.confidence,
            "metadata": dict(self.metadata) if self.metadata else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        """Deserialize AgentResponse from dictionary."""
        evidence_raw = data.get("evidence", [])
        evidence_items = [
            EvidenceItem.from_dict(e) if isinstance(e, dict) else e
            for e in evidence_raw
        ]
        prov_data = data.get("provenance")
        prov = ProvenanceRecord.from_dict(prov_data) if prov_data else None
        return cls(
            answer=data.get("answer", ""),
            evidence=evidence_items,
            limitations=list(data.get("limitations", [])),
            provenance=prov,
            status=data.get("status", "SUCCESS"),
            confidence=data.get("confidence", "HIGH"),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        """Serialize AgentResponse to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentResponse":
        """Deserialize AgentResponse from JSON string."""
        return cls.from_dict(json.loads(json_str))
