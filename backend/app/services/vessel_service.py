from typing import Optional

from sqlalchemy.orm import Session

from app.models.vessel import Vessel


def get_vessels(
    db: Session,
    vessel_class: Optional[str] = None,
    cargo_type: Optional[str] = None,
    quantity_tonnes: Optional[float] = None,
):
    query = db.query(Vessel).filter(Vessel.is_available.is_(True))

    if vessel_class:
        query = query.filter(
            Vessel.vessel_class.ilike(vessel_class)
        )

    if cargo_type:
        query = query.filter(
            Vessel.cargo_types.ilike(f"%{cargo_type}%")
        )

    if quantity_tonnes is not None:
        query = query.filter(
            Vessel.dwt >= quantity_tonnes
        )

    return query.order_by(Vessel.dwt.asc()).all()


def get_vessel_by_id(
    db: Session,
    vessel_id: int,
):
    return (
        db.query(Vessel)
        .filter(Vessel.id == vessel_id)
        .first()
    )


def check_cargo_compatibility(
    vessel: Vessel,
    cargo_type: str,
    quantity_tonnes: float,
):
    reasons = []
    feasible = True

    # Capacity check
    if vessel.dwt is None:
        feasible = False
        reasons.append("Vessel DWT data is unavailable.")
    elif quantity_tonnes > vessel.dwt:
        feasible = False
        reasons.append(
            f"Cargo quantity {quantity_tonnes} tonnes "
            f"exceeds vessel DWT {vessel.dwt} tonnes."
        )

    # Cargo type check
    if vessel.cargo_types:
        supported_types = [
            item.strip().lower()
            for item in vessel.cargo_types.split(",")
        ]

        if cargo_type.lower() not in supported_types:
            feasible = False
            reasons.append(
                f"Vessel does not support cargo type '{cargo_type}'."
            )
    else:
        feasible = False
        reasons.append("Vessel cargo compatibility data is unavailable.")

    if feasible:
        reasons.append(
            "Vessel capacity and cargo compatibility checks passed."
        )

    return {
        "feasible": feasible,
        "reasons": reasons,
    }