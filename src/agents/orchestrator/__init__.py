"""Stage 7.7 Multi-Agent Orchestrator package.

Exports:
    MultiAgentOrchestrationRequest
    MultiAgentOrchestrationResponse
    AgentSynthesisFinding
    MultiAgentOrchestrator
"""

from src.agents.orchestrator.contracts import (
    AgentSynthesisFinding,
    MultiAgentOrchestrationRequest,
    MultiAgentOrchestrationResponse,
)
from src.agents.orchestrator.service import MultiAgentOrchestrator

__all__ = [
    "AgentSynthesisFinding",
    "MultiAgentOrchestrationRequest",
    "MultiAgentOrchestrationResponse",
    "MultiAgentOrchestrator",
]
