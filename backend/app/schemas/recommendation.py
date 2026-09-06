from datetime import date
from typing import Any, Optional

from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    cargo_type: str
    quantity_tonnes: float
    origin_country: str
    destination_region: str
    arrival_date: date


class RecommendationResponse(BaseModel):
    strategy: str
    vessel_id: Optional[int] = None
    port_id: Optional[int] = None

    forecast: Optional[dict[str, Any]] = None
    cost: Optional[dict[str, Any]] = None
    risk: Optional[dict[str, Any]] = None

    reasons: list[str] = []
    alternatives: list[dict[str, Any]] = []