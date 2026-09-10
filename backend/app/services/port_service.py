from typing import Optional

from sqlalchemy.orm import Session

from app.models.port import Port


def get_ports(db, region=None, cargo_type=None):
    query = db.query(Port)

    if region:
        if region.lower() == "east coast india":
            query = query.filter(Port.country.ilike("India"))
        else:
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


def calculate_port_suitability_score(
    port: Port,
) -> Optional[float]:
    """
    Higher score = better port suitability.

    Uses:
    - Average waiting hours: 60%
    - Utilization: 40%
    """

    if (
        port.average_waiting_hours is None
        and port.utilization_percent is None
    ):
        return None

    scores = []

    if port.average_waiting_hours is not None:
        waiting_score = max(
            0.0,
            min(
                100.0,
                100.0
                - (port.average_waiting_hours / 36.0) * 100.0,
            ),
        )
        scores.append(waiting_score * 0.60)

    if port.utilization_percent is not None:
        utilization_score = max(
            0.0,
            min(
                100.0,
                100.0 - port.utilization_percent,
            ),
        )
        scores.append(utilization_score * 0.40)

    return round(sum(scores), 2)


def calculate_arrival_feasibility_score(
    port: Port,
    expected_delay_hours: Optional[float],
) -> Optional[float]:
    """
    Higher score = better arrival feasibility.

    Uses:
    - Expected waiting/delay: 70%
    - Port utilization: 30%

    This is a port-side feasibility proxy because
    route distance and voyage duration are not available.
    """

    if expected_delay_hours is None:
        return None

    delay_score = max(
        0.0,
        min(
            100.0,
            100.0
            - (expected_delay_hours / 36.0) * 100.0,
        ),
    )

    if port.utilization_percent is None:
        return round(delay_score, 2)

    utilization_score = max(
        0.0,
        min(
            100.0,
            100.0 - port.utilization_percent,
        ),
    )

    return round(
        delay_score * 0.70
        + utilization_score * 0.30,
        2,
    )


def check_port_vessel_compatibility(
    port: Port,
    vessel_loa_m: Optional[float],
    vessel_beam_m: Optional[float],
    vessel_draft_m: Optional[float],
):
    feasible = True
    reasons = []

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
