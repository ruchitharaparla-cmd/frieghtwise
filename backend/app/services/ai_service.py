from typing import Any, Optional

from app.agents.contracts import AgentContext
from app.agents.market.contracts import MarketAnalysisRequest
from app.agents.market.service import MarketAnalystService


def _to_dict(value: Any) -> Optional[dict[str, Any]]:
    """Safely convert supported model objects to dictionaries."""
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return None


class FreightWiseAIService:
    """
    Thin adapter between the FreightWise numerical decision engine
    and the Stage 7 Market Analyst.

    Stage 7 is explanatory only. It does not replace or modify
    authoritative forecasting, feasibility, cost, risk, or
    optimization results.
    """

    def __init__(self, is_testing: bool = False):
        self.market_analyst = MarketAnalystService(
            is_testing=is_testing
        )

    def explain_recommendation(
        self,
        recommendation,
        voyage=None,
        forecast=None,
        delay=None,
        congestion=None,
        feasibility=None,
        cost=None,
        optimization=None,
        risk=None,
        question=None,
    ):
        recommendation_data = _to_dict(recommendation) or {}
        voyage_data = _to_dict(voyage) or {}

        context = AgentContext(
            freight_forecast=_to_dict(forecast),
            delay_prediction=_to_dict(delay),
            congestion_prediction=_to_dict(congestion),
            feasibility_result=_to_dict(feasibility),
            cost_result=_to_dict(cost),
            optimization_result=_to_dict(optimization),
            evidence=[],
            metadata={
                "source": "freightwise-recommendation-engine",
                "voyage": voyage_data,
                "recommendation": recommendation_data,
                "risk_result": _to_dict(risk),
            },
        )

        if question is None:
            strategy = recommendation_data.get(
                "strategy",
                "UNKNOWN",
            )

            question = (
                f"Explain the FreightWise recommendation strategy "
                f"'{strategy}'. Use the supplied authoritative "
                "numerical pipeline outputs and retrieved evidence. "
                "Explain why the recommendation was selected, the "
                "important cost, risk and feasibility factors, and "
                "any limitations."
            )

        request = MarketAnalysisRequest(
            question=question,
            context=context,
            retrieval_query=None,
            max_evidence_items=5,
            include_limitations=True,
            metadata={
                "source": "freightwise-ai-service",
                "recommendation_strategy": recommendation_data.get(
                    "strategy",
                    "UNKNOWN",
                ),
            },
        )

        return self.market_analyst.analyze(
            request=request,
            context=context,
        )