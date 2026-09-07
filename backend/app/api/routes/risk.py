from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.services.risk_service import calculate_risk

router = APIRouter(tags=["Risk"])


class RiskRequest(BaseModel):
    congestion_score: Optional[float] = Field(default=None, ge=0, le=100)
    weather_score: Optional[float] = Field(default=None, ge=0, le=100)
    demurrage_score: Optional[float] = Field(default=None, ge=0, le=100)


@router.post("/risk")
def calculate_risk_endpoint(request: RiskRequest):
    return calculate_risk(
        congestion_score=request.congestion_score,
        weather_score=request.weather_score,
        demurrage_score=request.demurrage_score,
    )