from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    cargo_type: str
    quantity_tonnes: float = Field(gt=0)
    origin_country: str
    destination_region: str
    arrival_date: date

    # Required because the current FreightWise freight forecast
    # is expressed as USD/day and must be converted into voyage
    # freight cost using the charter duration.
    charter_duration_days: float = Field(
        gt=0,
    )


class RecommendationResponse(BaseModel):
    strategy: str
    vessel_id: int | None = None
    port_id: int | None = None

    forecast: dict[str, Any] | None = None
    cost: dict[str, Any] | None = None
    risk: dict[str, Any] | None = None

    # Overall optimization score.
    # Lower score = better option.
    score: float | None = None

    # Contribution of each optimization factor
    # to the overall score.
    score_breakdown: dict[str, float] = Field(
        default_factory=dict
    )

    reasons: list[str] = Field(
        default_factory=list
    )

    alternatives: list[dict[str, Any]] = Field(
        default_factory=list
    )

    # Stage 7 AI/RAG explanation layer.
    # This does not replace or modify the numerical recommendation.
    ai_analysis: dict[str, Any] | None = None