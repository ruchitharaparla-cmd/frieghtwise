"""Stage 7.5 Risk Analyst Model Provider Abstraction."""

from abc import ABC, abstractmethod
import os
from typing import List, Optional

from src.agents.contracts import AgentContext, AgentResponse, EvidenceItem, ProvenanceRecord
from src.agents.risk.contracts import RiskAnalysisRequest
from src.agents.risk.prompts import build_risk_analysis_prompt, RISK_ANALYST_SYSTEM_PROMPT


class BaseRiskAnalystModel(ABC):
    """Abstract base class for Risk Analyst LLM providers."""

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
        request: RiskAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        pass


class OpenAIRiskAnalystModel(BaseRiskAnalystModel):
    """Production OpenAI provider for Risk Agent."""

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
        request: RiskAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        if not self.api_key:
            return AgentResponse(
                answer="OpenAI API key missing. Risk LLM provider unavailable.",
                evidence=evidence or [],
                limitations=["Production Risk LLM provider unavailable."],
                status="PROVIDER_UNAVAILABLE",
                confidence="LOW",
                metadata={"error": "OPENAI_API_KEY_MISSING", "provider": "OpenAIRiskAnalystModel"}
            )

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            prompt = build_risk_analysis_prompt(request, context, evidence)
            res = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": RISK_ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            ans = res.choices[0].message.content or ""
            prov = ProvenanceRecord(
                record_id=f"prov_risk_openai_{request.question[:8]}",
                source="OpenAIRiskAnalystModel",
                source_type="MODEL",
                stage="Stage 7.5",
                model_name=self.model_name,
                model_version=self.model_version,
            )
            return AgentResponse(
                answer=ans,
                evidence=evidence or [],
                limitations=["AI-generated operational risk commentary."],
                provenance=prov,
                status="SUCCESS",
                confidence="HIGH",
            )
        except Exception as e:
            return AgentResponse(
                answer=f"OpenAI Risk LLM execution failed: {e}",
                evidence=evidence or [],
                limitations=[f"Provider error: {e}"],
                status="PROVIDER_UNAVAILABLE",
                confidence="LOW",
                metadata={"error": str(e)}
            )


class DeterministicTestRiskAnalystModel(BaseRiskAnalystModel):
    """TEST-ONLY Risk Analyst Model for offline unit tests."""

    def __init__(self, model_name: str = "test-deterministic-risk-agent", model_version: str = "1.0.0"):
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
        request: RiskAnalysisRequest,
        context: Optional[AgentContext] = None,
        evidence: Optional[List[EvidenceItem]] = None,
    ) -> AgentResponse:
        ev_items = evidence or (context.evidence if context else [])
        ans_parts: List[str] = [f"Risk Analysis Summary for query: '{request.question}'."]

        if context:
            if context.delay_prediction:
                hrs = context.delay_prediction.get("predicted_delay_hours") or context.delay_prediction.get("delay_hours")
                if hrs is not None:
                    ans_parts.append(f"Stage 3 turnaround delay model predicts {hrs} hours delay.")
            if context.congestion_prediction:
                scope = context.congestion_prediction.get("data_scope", "AUTHORIZED")
                ans_parts.append(f"Stage 3 congestion signal scope is {scope}.")
            if context.feasibility_result:
                st = context.feasibility_result.get("status") or context.feasibility_result.get("feasibility_status")
                if st:
                    ans_parts.append(f"Stage 4 feasibility status is {st}.")

        if ev_items:
            ans_parts.append(f"Supporting RAG risk evidence items ({len(ev_items)}) retrieved.")

        prov = ProvenanceRecord(
            record_id=f"prov_test_{self.model_name}",
            source="DeterministicTestRiskAnalystModel",
            source_type="MODEL",
            stage="Stage 7.5 Test",
            model_name=self.model_name,
            model_version=self.model_version,
        )

        return AgentResponse(
            answer=" ".join(ans_parts),
            evidence=ev_items,
            limitations=["Deterministic test risk provider."],
            provenance=prov,
            status="SUCCESS",
            confidence="HIGH",
        )


def get_risk_analyst_model(is_testing: bool = False, provider_name: str = "openai") -> BaseRiskAnalystModel:
    if is_testing:
        return DeterministicTestRiskAnalystModel()
    if provider_name.lower() == "openai":
        return OpenAIRiskAnalystModel()
    raise ValueError(f"Unknown risk analyst model provider '{provider_name}'.")
