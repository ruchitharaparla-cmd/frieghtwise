from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    origin_country: str
    destination_region: str
    cargo_type: str
    vessel_class: str
    forecast_date: date


class ForecastResponse(BaseModel):
    forecast_rate: Optional[float] = None
    currency: str = "USD"
    unit: str = "per_metric_tonne"
    forecast_date: date
    model_version: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    data_status: str = "UNAVAILABLE"