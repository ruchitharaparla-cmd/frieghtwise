from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.cost_service import calculate_cost


router = APIRouter(tags=["Cost"])


class CostRequest(BaseModel):
    quantity_tonnes: float = Field(gt=0)

    freight_rate: Optional[float] = Field(
        default=None,
        ge=0,
    )

    freight_rate_unit: str = "USD/day"

    voyage_duration_days: Optional[float] = Field(
        default=None,
        gt=0,
    )

    bunker_cost: Optional[float] = Field(
        default=None,
        ge=0,
    )

    port_cost: Optional[float] = Field(
        default=None,
        ge=0,
    )

    expected_delay_hours: Optional[float] = Field(
        default=None,
        ge=0,
    )

    demurrage_rate_per_day: Optional[float] = Field(
        default=None,
        ge=0,
    )


@router.post("/cost")
def calculate_cost_endpoint(request: CostRequest):
    return calculate_cost(
        quantity_tonnes=request.quantity_tonnes,
        freight_rate=request.freight_rate,
        bunker_cost=request.bunker_cost,
        port_cost=request.port_cost,
        expected_delay_hours=request.expected_delay_hours,
        demurrage_rate_per_day=request.demurrage_rate_per_day,
        freight_rate_unit=request.freight_rate_unit,
        voyage_duration_days=request.voyage_duration_days,
    )
