from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VoyageCreate(BaseModel):
    cargo_type: str
    quantity_tonnes: float = Field(gt=0)

    origin_country: str
    destination_region: str

    arrival_date: date

    charter_start_date: Optional[date] = None
    charter_end_date: Optional[date] = None


class VoyageResponse(BaseModel):
    id: int

    cargo_type: str
    quantity_tonnes: float

    origin_country: str
    destination_region: str

    arrival_date: date

    status: str

    model_config = ConfigDict(from_attributes=True)