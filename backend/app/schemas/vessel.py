from typing import Optional

from pydantic import BaseModel, ConfigDict


class VesselResponse(BaseModel):
    id: int
    name: str
    vessel_class: str
    dwt: Optional[float] = None
    loa_m: Optional[float] = None
    beam_m: Optional[float] = None
    draft_m: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class VesselListResponse(BaseModel):
    vessels: list[VesselResponse]


class CompatibilityRequest(BaseModel):
    vessel_id: int
    cargo_type: str
    quantity_tonnes: float


class CompatibilityResponse(BaseModel):
    feasible: bool
    reasons: list[str]