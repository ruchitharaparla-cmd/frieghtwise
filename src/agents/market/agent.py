"""Stage 7.4 Market Analyst LLM Provider Abstraction.

Supports pluggable LLM providers (e.g., OpenAIMarketAnalystModel) and a test-only
deterministic provider (DeterministicTestMarketAnalystModel).

Safeguard: Never silently fall back to DeterministicTestMarketAnalystModel in production.
If a production LLM provider is unavailable, return an explicit PROVIDER_UNAVAILABLE status/error.
"""

from abc import ABC, abstractmethod
import os
from typing import List, Optional

from src.agents.contracts import AgentContext, AgentResponse, EvidenceItem, ProvenanceRecord
from src.agents.market.contracts import MarketAnalysisRequest, MarketFinding
from src.agents.market.prompts import build_market_analysis_prompt, MARKET_ANALYST_SYSTEM_PROMPT


class BaseMarketAnalystModel(ABC):
    """Abstract base class for Market Analyst LLM providers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier string."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return the model version string."""
        pass

    @abstractmethod
    def generate(
        self,
        request: MarketAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        """Generate structured analytical response from request, context, and evidence."""
        pass


class OpenAIMarketAnalystModel(BaseMarketAnalystModel):
    """Production OpenAI LLM provider wrapper.

    If OpenAI API key or package is unavailable, returns PROVIDER_UNAVAILABLE status.
    Will NEVER fall back to fake generated test responses.
    """

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self._model_name = model_name
        self._model_version = "1.0.0"
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    def generate(
        self,
        request: MarketAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        """Generate response via OpenAI API, or return PROVIDER_UNAVAILABLE if key/pkg missing."""
        if not self.api_key:
            return AgentResponse(
                answer="OpenAI API key is missing or unconfigured. Provider is unavailable.",
                evidence=evidence or [],
                limitations=["Production LLM provider unavailable."],
                status="PROVIDER_UNAVAILABLE",
                confidence="LOW",
                metadata={"error": "OPENAI_API_KEY_MISSING", "provider": "OpenAIMarketAnalystModel"}
            )

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            prompt = build_market_analysis_prompt(request, context, evidence)

            res = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": MARKET_ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            ans_text = res.choices[0].message.content or ""

            prov = ProvenanceRecord(
                record_id=f"prov_openai_{request.question[:8]}",
                source="OpenAIMarketAnalystModel",
                source_type="MODEL",
                stage="Stage 7.4",
                model_name=self.model_name,
                model_version=self.model_version,
            )

            return AgentResponse(
                answer=ans_text,
                evidence=evidence or [],
                limitations=["AI-generated market commentary downstream of Stage 2-6 pipeline."],
                provenance=prov,
                status="SUCCESS",
                confidence="HIGH",
                metadata={"model": self.model_name}
            )
        except Exception as e:
            return AgentResponse(
                answer=f"OpenAI LLM provider execution failed: {e}",
                evidence=evidence or [],
                limitations=[f"Provider error: {e}"],
                status="PROVIDER_UNAVAILABLE",
                confidence="LOW",
                metadata={"error": str(e), "provider": "OpenAIMarketAnalystModel"}
            )


class DeterministicTestMarketAnalystModel(BaseMarketAnalystModel):
    """TEST-ONLY Market Analyst Model for offline unit tests and test fixtures.

    WARNING: Must NEVER be used as the production AI model in deployment.
    Extracts authoritative Stage 2-6 numbers and RAG evidence IDs deterministically.
    """

    def __init__(self, model_name: str = "test-deterministic-market-agent", model_version: str = "1.0.0"):
        self._model_name = model_name
        self._model_version = model_version

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> str:
        return self._model_version

    def generate(
        self,
        request: MarketAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        """Generate deterministic analytical text for unit tests."""
        ev_items = evidence or (context.evidence if context else [])

        ans_parts: List[str] = [
            f"Market Analysis Summary for query: '{request.question}'."
        ]

        # Extract Stage 2-6 numbers cleanly if context present
        if context:
            if context.freight_forecast:
                rate = context.freight_forecast.get("predicted_freight_rate") or context.freight_forecast.get("predicted_rate")
                if rate is not None:
                    ans_parts.append(f"Stage 2 freight forecast indicates predicted rate of {rate} USD/day.")
            if context.delay_prediction:
                hrs = context.delay_prediction.get("predicted_delay_hours") or context.delay_prediction.get("delay_hours")
                if hrs is not None:
                    ans_parts.append(f"Stage 3 delay model predicts turnaround delay of {hrs} hours.")
            if context.congestion_prediction:
                scope = context.congestion_prediction.get("data_scope", "AUTHORIZED")
                ans_parts.append(f"Stage 3 congestion signal scope is {scope}.")
            if context.feasibility_result:
                st = context.feasibility_result.get("status") or context.feasibility_result.get("feasibility_status")
                if st:
                    ans_parts.append(f"Stage 4 feasibility evaluation status is {st}.")
            if context.cost_result:
                c = context.cost_result.get("total_charter_cost") or context.cost_result.get("total_cost")
                if c is not None:
                    ans_parts.append(f"Stage 5 voyage charter cost engine reports total cost of {c} USD.")
            if context.optimization_result:
                plan = context.optimization_result.get("selected_vessel_id") or context.optimization_result.get("optimal_schedule")
                if plan:
                    ans_parts.append(f"Stage 6 CP-SAT optimizer selected allocation plan for {plan}.")

        if ev_items:
            ans_parts.append(f"Supporting RAG evidence items ({len(ev_items)}) retrieved from Stage 7.3 knowledge base.")

        ans_text = " ".join(ans_parts)

        prov = ProvenanceRecord(
            record_id=f"prov_test_{self.model_name}",
            source="DeterministicTestMarketAnalystModel",
            source_type="MODEL",
            stage="Stage 7.4 Test",
            model_name=self.model_name,
            model_version=self.model_version,
        )

        return AgentResponse(
            answer=ans_text,
            evidence=ev_items,
            limitations=[
                "Deterministic test provider for unit tests only.",
                "Authoritative Stage 2-6 pipeline numbers preserved without calculation."
            ],
            provenance=prov,
            status="SUCCESS",
            confidence="HIGH",
            metadata={"test_mode": True}
        )


def get_market_analyst_model(is_testing: bool = False, provider_name: str = "openai") -> BaseMarketAnalystModel:
    """Factory for obtaining Market Analyst model instance.

    Args:
        is_testing: If True, returns DeterministicTestMarketAnalystModel for unit tests.
                   If False (default), returns production provider (OpenAIMarketAnalystModel).
    """
    if is_testing:
        return DeterministicTestMarketAnalystModel()
    if provider_name.lower() == "openai":
        return OpenAIMarketAnalystModel()
    raise ValueError(f"Unknown market analyst model provider '{provider_name}'.")
