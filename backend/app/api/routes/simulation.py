from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.decision_engine_service import run_decision_engine


router = APIRouter(tags=["Simulation"])


class Scenario(BaseModel):
    cargo_type: str
    quantity_tonnes: float = Field(gt=0)
    origin_country: str
    destination_region: str
    arrival_date: date
    charter_duration_days: Optional[float] = Field(
        default=None,
        gt=0,
    )


class SimulationRequest(BaseModel):
    base_scenario: Scenario
    changes: dict[str, Any] = {}


@router.post("/simulation")
def run_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db),
):
    base = request.base_scenario.model_dump()

    modified = base.copy()
    modified.update(request.changes)

    base_result = run_decision_engine(
        db=db,
        cargo_type=base["cargo_type"],
        quantity_tonnes=base["quantity_tonnes"],
        origin_country=base["origin_country"],
        destination_region=base["destination_region"],
        arrival_date=base["arrival_date"],
        charter_duration_days=base.get("charter_duration_days"),
    )

    modified_result = run_decision_engine(
        db=db,
        cargo_type=modified["cargo_type"],
        quantity_tonnes=modified["quantity_tonnes"],
        origin_country=modified["origin_country"],
        destination_region=modified["destination_region"],
        arrival_date=modified["arrival_date"],
        charter_duration_days=modified.get("charter_duration_days"),
    )

    base_cost = (
        base_result.get("cost") or {}
    ).get("total_landed_cost")

    modified_cost = (
        modified_result.get("cost") or {}
    ).get("total_landed_cost")

    cost_difference = None

    if base_cost is not None and modified_cost is not None:
        cost_difference = round(
            modified_cost - base_cost,
            2,
        )

    base_recommendation = {
        "strategy": base_result.get("strategy"),
        "vessel_id": base_result.get("vessel_id"),
        "port_id": base_result.get("port_id"),
    }

    modified_recommendation = {
        "strategy": modified_result.get("strategy"),
        "vessel_id": modified_result.get("vessel_id"),
        "port_id": modified_result.get("port_id"),
    }

    recommendation_changed = (
        base_recommendation != modified_recommendation
    )

    return {
        "base_scenario": {
            "recommendation": base_recommendation,
            "total_landed_cost": base_cost,
            "risk": base_result.get("risk"),
        },
        "modified_scenario": {
            "recommendation": modified_recommendation,
            "total_landed_cost": modified_cost,
            "risk": modified_result.get("risk"),
        },
        "differences": {
            "cost_difference": cost_difference,
            "recommendation_changed": recommendation_changed,
        },
        "recommendation_changed": recommendation_changed,
    }