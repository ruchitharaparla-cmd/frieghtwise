from sqlalchemy.orm import Session

from app.services.vessel_service import get_vessels
from app.services.port_service import get_ports, check_port_vessel_compatibility
from app.services.forecast_service import get_freight_forecast
from app.services.congestion_service import (
    calculate_congestion_score,
    estimate_delay_hours,
)
from app.services.cost_service import calculate_cost
from app.services.risk_service import calculate_risk
from app.services.recommendation_service import generate_recommendation
from app.schemas.forecast import ForecastRequest


def run_decision_engine(
    db: Session,
    cargo_type: str,
    quantity_tonnes: float,
    origin_country: str,
    destination_region: str,
    arrival_date,
):
    vessels = get_vessels(
        db=db,
        cargo_type=cargo_type,
        quantity_tonnes=quantity_tonnes,
    )

    ports = get_ports(
        db=db,
        region=destination_region,
        cargo_type=cargo_type,
    )

    options = []

    for vessel in vessels:
        for port in ports:

            compatibility = check_port_vessel_compatibility(
                port=port,
                vessel_loa_m=vessel.loa_m,
                vessel_beam_m=vessel.beam_m,
                vessel_draft_m=vessel.draft_m,
            )

            if not compatibility["feasible"]:
                continue

            forecast = get_freight_forecast(
                db=db,
                request=ForecastRequest(
                    origin_country=origin_country,
                    destination_region=destination_region,
                    cargo_type=cargo_type,
                    vessel_class=vessel.vessel_class,
                    forecast_date=arrival_date,
                ),
            )

            congestion = calculate_congestion_score(
                port.average_waiting_hours
            )

            delay_hours = estimate_delay_hours(
                port.average_waiting_hours
            )

            risk = calculate_risk(
                congestion_score=congestion["score"],
            )

            cost = calculate_cost(
                quantity_tonnes=quantity_tonnes,
                freight_rate=forecast["forecast_rate"],
                bunker_cost=None,
                port_cost=None,
                expected_delay_hours=delay_hours,
                demurrage_rate_per_day=None,
            )

            options.append(
                {
                    "feasible": True,
                    "vessel_id": vessel.id,
                    "port_id": port.id,
                    "vessel_class": vessel.vessel_class,
                    "freight_rate": forecast["forecast_rate"],
                    "expected_delay_hours": delay_hours,
                    "overall_risk": risk["overall_risk"],
                    "port_suitability_score": congestion["score"],
                    "arrival_feasibility_score": 0,
                    "total_landed_cost": cost["total_landed_cost"],
                    "forecast": forecast,
                    "cost": cost,
                    "risk": risk,
                    "rejection_reasons": [],
                }
            )

    return generate_recommendation(options=options)