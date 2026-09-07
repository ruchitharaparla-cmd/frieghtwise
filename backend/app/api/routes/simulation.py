from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.services.cost_service import calculate_cost
from app.services.risk_service import calculate_risk

router = APIRouter(tags=["Simulation"])


class Scenario(BaseModel):
    quantity_tonnes: float = Field(gt=0)
    freight_rate: Optional[float] = Field(default=None, ge=0)
    bunker_cost: Optional[float] = Field(default=None, ge=0)
    port_cost: Optional[float] = Field(default=None, ge=0)
    expected_delay_hours: Optional[float] = Field(default=None, ge=0)
    demurrage_rate_per_day: Optional[float] = Field(default=None, ge=0)
    congestion_score: Optional[float] = Field(default=None, ge=0, le=100)
    weather_score: Optional[float] = Field(default=None, ge=0, le=100)
    demurrage_score: Optional[float] = Field(default=None, ge=0, le=100)


class SimulationRequest(BaseModel):
    base_scenario: Scenario
    changes: dict = {}


@router.post("/simulation")
def run_simulation(request: SimulationRequest):

    base = request.base_scenario.model_dump()

    modified = base.copy()
    modified.update(request.changes)

    base_cost = calculate_cost(
        quantity_tonnes=base["quantity_tonnes"],
        freight_rate=base["freight_rate"],
        bunker_cost=base["bunker_cost"],
        port_cost=base["port_cost"],
        expected_delay_hours=base["expected_delay_hours"],
        demurrage_rate_per_day=base["demurrage_rate_per_day"],
    )

    modified_cost = calculate_cost(
        quantity_tonnes=modified["quantity_tonnes"],
        freight_rate=modified["freight_rate"],
        bunker_cost=modified["bunker_cost"],
        port_cost=modified["port_cost"],
        expected_delay_hours=modified["expected_delay_hours"],
        demurrage_rate_per_day=modified["demurrage_rate_per_day"],
    )

    base_risk = calculate_risk(
        congestion_score=base["congestion_score"],
        weather_score=base["weather_score"],
        demurrage_score=base["demurrage_score"],
    )

    modified_risk = calculate_risk(
        congestion_score=modified["congestion_score"],
        weather_score=modified["weather_score"],
        demurrage_score=modified["demurrage_score"],
    )

    base_total = base_cost["total_landed_cost"]
    modified_total = modified_cost["total_landed_cost"]

    cost_difference = None
    if base_total is not None and modified_total is not None:
        cost_difference = modified_total - base_total

    return {
        "base_scenario": {
            "total_landed_cost": base_total,
            "risk_level": base_risk["risk_level"],
        },
        "modified_scenario": {
            "total_landed_cost": modified_total,
            "risk_level": modified_risk["risk_level"],
        },
        "differences": {
            "cost_difference": cost_difference,
            "risk_changed": (
                base_risk["risk_level"] != modified_risk["risk_level"]
            ),
        },
        "recommendation_changed": (
            base_risk["risk_level"] != modified_risk["risk_level"]
            or cost_difference is not None and cost_difference > 0
        ),
    }