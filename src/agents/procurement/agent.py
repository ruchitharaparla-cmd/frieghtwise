"""Stage 7.6 Procurement Agent Model Provider Abstraction."""

from abc import ABC, abstractmethod
import os
from typing import List, Optional

from src.agents.contracts import AgentContext, AgentResponse, EvidenceItem, ProvenanceRecord
from src.agents.procurement.contracts import ProcurementAnalysisRequest
from src.agents.procurement.prompts import build_procurement_analysis_prompt, PROCUREMENT_STRATEGY_SYSTEM_PROMPT


class BaseProcurementModel(ABC):
    """Abstract base class for Procurement Strategy LLM providers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        pass

    @abstractmethod
    def generate(
        self,
        request: ProcurementAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        pass


class OpenAIProcurementModel(BaseProcurementModel):
    """Production OpenAI provider for Procurement Agent."""

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
        request: ProcurementAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        if not self.api_key:
            return AgentResponse(
                answer="OpenAI API key missing. Procurement LLM provider unavailable.",
                evidence=evidence or [],
                limitations=["Production Procurement LLM provider unavailable."],
                status="PROVIDER_UNAVAILABLE",
                confidence="LOW",
                metadata={"error": "OPENAI_API_KEY_MISSING", "provider": "OpenAIProcurementModel"}
            )

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            prompt = build_procurement_analysis_prompt(request, context, evidence)
            res = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": PROCUREMENT_STRATEGY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            ans = res.choices[0].message.content or ""
            prov = ProvenanceRecord(
                record_id=f"prov_proc_openai_{request.question[:8]}",
                source="OpenAIProcurementModel",
                source_type="MODEL",
                stage="Stage 7.6",
                model_name=self.model_name,
                model_version=self.model_version,
            )
            return AgentResponse(
                answer=ans,
                evidence=evidence or [],
                limitations=["AI-generated charter strategy commentary."],
                provenance=prov,
                status="SUCCESS",
                confidence="HIGH",
            )
        except Exception as e:
            return AgentResponse(
                answer=f"OpenAI Procurement LLM execution failed: {e}",
                evidence=evidence or [],
                limitations=[f"Provider error: {e}"],
                status="PROVIDER_UNAVAILABLE",
                confidence="LOW",
                metadata={"error": str(e)}
            )


class DeterministicTestProcurementModel(BaseProcurementModel):
    """TEST-ONLY Procurement Model for offline unit tests."""

    def __init__(self, model_name: str = "test-deterministic-procurement-agent", model_version: str = "1.0.0"):
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
        request: ProcurementAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        ev_items = evidence or (context.evidence if context else [])
        ans_parts: List[str] = [f"Procurement Strategy Summary for query: '{request.question}'."]

        if context:
            if context.cost_result:
                cost = context.cost_result.get("total_charter_cost") or context.cost_result.get("total_cost")
                if cost is not None:
                    ans_parts.append(f"Stage 5 voyage charter cost engine reports total cost of {cost} USD.")
            if context.optimization_result:
                vessel = context.optimization_result.get("selected_vessel_id") or context.optimization_result.get("optimal_schedule")
                if vessel:
                    ans_parts.append(f"Stage 6 CP-SAT optimizer selected allocation plan for {vessel}.")

        if ev_items:
            ans_parts.append(f"Supporting RAG procurement evidence items ({len(ev_items)}) retrieved.")

        prov = ProvenanceRecord(
            record_id=f"prov_test_{self.model_name}",
            source="DeterministicTestProcurementModel",
            source_type="MODEL",
            stage="Stage 7.6 Test",
            model_name=self.model_name,
            model_version=self.model_version,
        )

        return AgentResponse(
            answer=" ".join(ans_parts),
            evidence=ev_items,
            limitations=["Deterministic test procurement provider."],
            provenance=prov,
            status="SUCCESS",
            confidence="HIGH",
        )


def get_procurement_model(is_testing: bool = False, provider_name: str = "openai") -> BaseProcurementModel:
    if is_testing:
        return DeterministicTestProcurementModel()
    if provider_name.lower() == "openai":
        return OpenAIProcurementModel()
    raise ValueError(f"Unknown procurement model provider '{provider_name}'.")
