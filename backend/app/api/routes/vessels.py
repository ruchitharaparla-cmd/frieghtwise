from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.vessel import (
    CompatibilityRequest,
    CompatibilityResponse,
    VesselListResponse,
)
from app.services.vessel_service import (
    check_cargo_compatibility,
    get_vessel_by_id,
    get_vessels,
)
from app.services.port_service import (
    get_port_by_id,
    check_port_vessel_compatibility,
)


router = APIRouter(tags=["Vessels"])


@router.get("/vessels", response_model=VesselListResponse)
def list_vessels(
    vessel_class: Optional[str] = Query(default=None),
    cargo_type: Optional[str] = Query(default=None),
    quantity_tonnes: Optional[float] = Query(
        default=None,
        gt=0,
    ),
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

    port = get_port_by_id(
        db=db,
        port_id=request.port_id,
    )

    if port is None:
        return {
            "feasible": False,
            "reasons": [
                f"Port with id {request.port_id} was not found."
            ],
        }

    reasons = []
    feasible = True

    cargo_check = check_cargo_compatibility(
        vessel=vessel,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
    )

    if not cargo_check["feasible"]:
        feasible = False

    reasons.extend(cargo_check["reasons"])

    port_check = check_port_vessel_compatibility(
        port=port,
        vessel_loa_m=vessel.loa_m,
        vessel_beam_m=vessel.beam_m,
        vessel_draft_m=vessel.draft_m,
    )

    if not port_check["feasible"]:
        feasible = False

    reasons.extend(port_check["reasons"])

    if feasible:
        reasons = [
            "Cargo compatibility, vessel capacity, and port physical constraints passed."
        ]

    return {
        "feasible": feasible,
        "reasons": reasons,
    }