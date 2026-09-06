from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vessel import (
    CompatibilityRequest,
    CompatibilityResponse,
    VesselListResponse,
    VesselResponse,
)
from app.services.vessel_service import (
    check_cargo_compatibility,
    get_vessel_by_id,
    get_vessels,
)

router = APIRouter(tags=["Vessels"])


@router.get("/vessels", response_model=VesselListResponse)
def list_vessels(
    vessel_class: Optional[str] = Query(default=None),
    cargo_type: Optional[str] = Query(default=None),
    quantity_tonnes: Optional[float] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    vessels = get_vessels(
        db=db,
        vessel_class=vessel_class,
        cargo_type=cargo_type,
        quantity_tonnes=quantity_tonnes,
    )

    return {"vessels": vessels}


@router.post(
    "/compatibility",
    response_model=CompatibilityResponse,
)
def check_compatibility(
    request: CompatibilityRequest,
    db: Session = Depends(get_db),
):
    vessel = get_vessel_by_id(
        db=db,
        vessel_id=request.vessel_id,
    )

    if vessel is None:
        return {
            "feasible": False,
            "reasons": [
                f"Vessel with id {request.vessel_id} was not found."
            ],
        }

    return check_cargo_compatibility(
        vessel=vessel,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
    )