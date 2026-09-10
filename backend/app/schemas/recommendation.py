from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    cargo_type: str
    quantity_tonnes: float = Field(gt=0)
    origin_country: str
    destination_region: str
    arrival_date: date

    # Required when a USD/day freight benchmark is converted
    # into a voyage freight cost.
    charter_duration_days: Optional[float] = Field(
        default=None,
        gt=0,
    )


class RecommendationResponse(BaseModel):
    strategy: str
    vessel_id: Optional[int] = None
    port_id: Optional[int] = None

    forecast: Optional[dict[str, Any]] = None
    cost: Optional[dict[str, Any]] = None
    risk: Optional[dict[str, Any]] = None

    # Overall optimization score.
    # Lower score = better option.
    score: Optional[float] = None

    # Contribution of each optimization factor
    # to the overall score.
    score_breakdown: dict[str, float] = Field(
        default_factory=dict
    )

    reasons: list[str] = Field(default_factory=list)
    alternatives: list[dict[str, Any]] = Field(default_factory=list)

    # Stage 7 AI/RAG explanation layer.
    # This does not replace or modify the numerical recommendation.
    ai_analysis: Optional[dict[str, Any]] = None