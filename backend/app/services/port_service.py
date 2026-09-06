from typing import Optional

from sqlalchemy.orm import Session

from app.models.port import Port


def get_ports(
    db: Session,
    region: Optional[str] = None,
    cargo_type: Optional[str] = None,
):
    query = db.query(Port)

    if region:
        query = query.filter(
            Port.state.ilike(f"%{region}%")
        )

    if cargo_type:
        query = query.filter(
            Port.cargo_types.ilike(f"%{cargo_type}%")
        )

    return query.order_by(Port.name.asc()).all()


def get_port_by_id(
    db: Session,
    port_id: int,
):
    return (
        db.query(Port)
        .filter(Port.id == port_id)
        .first()
    )


def check_port_vessel_compatibility(
    port: Port,
    vessel_loa_m: Optional[float],
    vessel_beam_m: Optional[float],
    vessel_draft_m: Optional[float],
):
    feasible = True
    reasons = []

    if vessel_loa_m is not None and port.max_loa_m is not None:
        if vessel_loa_m > port.max_loa_m:
            feasible = False
            reasons.append(
                f"Vessel LOA {vessel_loa_m}m exceeds "
                f"port limit {port.max_loa_m}m."
            )

    if vessel_beam_m is not None and port.max_beam_m is not None:
        if vessel_beam_m > port.max_beam_m:
            feasible = False
            reasons.append(
                f"Vessel beam {vessel_beam_m}m exceeds "
                f"port limit {port.max_beam_m}m."
            )

    if vessel_draft_m is not None and port.max_draft_m is not None:
        if vessel_draft_m > port.max_draft_m:
            feasible = False
            reasons.append(
                f"Vessel draft {vessel_draft_m}m exceeds "
                f"port limit {port.max_draft_m}m."
            )

    if (
        vessel_loa_m is None
        and vessel_beam_m is None
        and vessel_draft_m is None
    ):
        feasible = False
        reasons.append(
            "Vessel dimension data is unavailable."
        )

    if feasible:
        reasons.append(
            "Vessel dimensions satisfy available port constraints."
        )

    return {
        "feasible": feasible,
        "reasons": reasons,
    }