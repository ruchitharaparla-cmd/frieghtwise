from typing import Optional

from pydantic import BaseModel, ConfigDict


class PortResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    state: Optional[str] = None
    country: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    max_draft_m: Optional[float] = None
    max_loa_m: Optional[float] = None
    max_beam_m: Optional[float] = None

    annual_capacity_tonnes: Optional[float] = None
    utilization_percent: Optional[float] = None
    average_waiting_hours: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PortListResponse(BaseModel):
    ports: list[PortResponse]