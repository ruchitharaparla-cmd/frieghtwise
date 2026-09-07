"""
FreightWise Stage 7 â€” AI Agents + RAG Layer Foundation.

Provides typed data contracts, context builders, safety validation boundaries,
and provenance tracking helpers.
"""

from src.agents.contracts import (
    EvidenceItem,
    AgentContext,
    AgentRequest,
    AgentResponse,
    ProvenanceRecord,
)
from src.agents.context import (
    build_agent_context,
)
from src.agents.provenance import (
    create_provenance_record,
    attach_provenance_to_evidence,
    extract_provenance_chain,
)
from src.agents.safety import (
    validate_agent_response,
    verify_authoritative_immutability,
    verify_data_scope,
    verify_data_unavailability,
    SafetyCheckResult,
    AgentSafetyError,
)

__all__ = [
    "EvidenceItem",
    "AgentContext",
    "AgentRequest",
    "AgentResponse",
    "ProvenanceRecord",
    "build_agent_context",
    "create_provenance_record",
    "attach_provenance_to_evidence",
    "extract_provenance_chain",
    "validate_agent_response",
    "verify_authoritative_immutability",
    "verify_data_scope",
    "verify_data_unavailability",
    "SafetyCheckResult",
    "AgentSafetyError",
]
