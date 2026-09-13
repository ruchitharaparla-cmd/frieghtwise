from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FreightTrendPoint(BaseModel):
    date: date
    rate: float
    value_type: str = "OBSERVED"


class FreightTrendRoute(BaseModel):
    origin_country: str
    destination_region: str
    display_name: str


class FreightTrendSource(BaseModel):
    name: Optional[str] = None
    data_status: str = "UNKNOWN"


class FreightTrendResponse(BaseModel):
    data_status: str
    currency: str = "USD"
    unit: str = "per_metric_tonne"

    route: FreightTrendRoute

    current_rate: Optional[float] = None
    previous_rate: Optional[float] = None
    change_7d: Optional[float] = None
    market_direction: str = "UNKNOWN"

    trend: list[FreightTrendPoint] = Field(default_factory=list)

    source: FreightTrendSource
    message: Optional[str] = None
