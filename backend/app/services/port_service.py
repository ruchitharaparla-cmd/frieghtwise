from typing import Optional

from sqlalchemy.orm import Session

from app.models.port import Port
def get_ports(db, region=None, cargo_type=None):
    query = db.query(Port)

    if region:
        if region.lower() == "east coast india":
            query = query.filter(Port.country.ilike("India"))
        else:
            query = query.filter(Port.state.ilike(f"%{region}%"))

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

    # LOA check
    if port.max_loa_m is None:
        feasible = False
        reasons.append("Port maximum LOA data is unavailable.")
    elif vessel_loa_m is None:
        feasible = False
        reasons.append("Vessel LOA data is unavailable.")
    elif vessel_loa_m > port.max_loa_m:
        feasible = False
        reasons.append(
            f"Vessel LOA {vessel_loa_m}m exceeds "
            f"port limit {port.max_loa_m}m."
        )

    # Beam check
    if port.max_beam_m is None:
        feasible = False
        reasons.append("Port maximum beam data is unavailable.")
    elif vessel_beam_m is None:
        feasible = False
        reasons.append("Vessel beam data is unavailable.")
    elif vessel_beam_m > port.max_beam_m:
        feasible = False
        reasons.append(
            f"Vessel beam {vessel_beam_m}m exceeds "
            f"port limit {port.max_beam_m}m."
        )

    # Draft check
    if port.max_draft_m is None:
        feasible = False
        reasons.append("Port maximum draft data is unavailable.")
    elif vessel_draft_m is None:
        feasible = False
        reasons.append("Vessel draft data is unavailable.")
    elif vessel_draft_m > port.max_draft_m:
        feasible = False
        reasons.append(
            f"Vessel draft {vessel_draft_m}m exceeds "
            f"port limit {port.max_draft_m}m."
        )

    if feasible:
        reasons.append(
            "Vessel dimensions satisfy all available port constraints."
        )

    return {
        "feasible": feasible,
        "reasons": reasons,
    }
