from sqlalchemy.orm import Session

from app.schemas.forecast import ForecastRequest
from app.services.vessel_service import get_vessels
from app.services.port_service import (
    get_ports,
    check_port_vessel_compatibility,
)
from app.services.forecast_service import get_freight_forecast
from app.services.congestion_service import (
    calculate_congestion_score,
    estimate_delay_hours,
)
from app.services.cost_service import calculate_cost
from app.services.risk_service import calculate_risk
from app.services.recommendation_service import generate_recommendation
from app.integrations.weather import get_weather_risk




# Prototype cost assumptions.
# These are estimated values, not live market data.
PROTOTYPE_BUNKER_COST_USD = 300000.0
PROTOTYPE_PORT_COST_USD = 100000.0
PROTOTYPE_DEMURRAGE_RATE_USD_PER_DAY = 20000.0

def calculate_arrival_feasibility_score(
    port,
    vessel_loa_m: float,
    vessel_beam_m: float,
    vessel_draft_m: float,
) -> float | None:
    """
    Calculate a vessel-port arrival feasibility score.

    Score interpretation:
        100 = excellent dimensional clearance
        0   = very poor dimensional clearance

    Higher is better.

    This is a FreightWise-derived engineering score.
    It is not an official port authority safety threshold.
    """

    required_values = [
        port.max_loa_m,
        port.max_beam_m,
        port.max_draft_m,
        vessel_loa_m,
        vessel_beam_m,
        vessel_draft_m,
    ]

    if any(value is None for value in required_values):
        return None

    # ---------------------------------------------------------
    # DIMENSIONAL CLEARANCE
    # ---------------------------------------------------------

    loa_margin = (
        (port.max_loa_m - vessel_loa_m)
        / port.max_loa_m
    ) * 100

    beam_margin = (
        (port.max_beam_m - vessel_beam_m)
        / port.max_beam_m
    ) * 100

    draft_margin = (
        (port.max_draft_m - vessel_draft_m)
        / port.max_draft_m
    ) * 100

    # ---------------------------------------------------------
    # CONVERT CLEARANCE INTO 0-100 FEASIBILITY
    #
    # More clearance = higher score.
    # ---------------------------------------------------------

    loa_score = max(
        0.0,
        min(
            100.0,
            loa_margin * 5.0,
        ),
    )

    beam_score = max(
        0.0,
        min(
            100.0,
            beam_margin * 5.0,
        ),
    )

    draft_score = max(
        0.0,
        min(
            100.0,
            draft_margin * 5.0,
        ),
    )

    # ---------------------------------------------------------
    # WEIGHTED FEASIBILITY SCORE
    #
    # Draft receives the highest weight because vertical
    # clearance is particularly important for port access.
    # ---------------------------------------------------------

    score = (
        loa_score * 0.30
        + beam_score * 0.25
        + draft_score * 0.45
    )

    return round(
        max(
            0.0,
            min(100.0, score),
        ),
        2,
    )


def run_decision_engine(
    db: Session,
    cargo_type: str,
    quantity_tonnes: float,
    origin_country: str,
    destination_region: str,
    arrival_date,
    charter_duration_days=None,
    vessel_id=None,
    port_id=None,
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

    if vessel_id is not None:
        vessels = [v for v in vessels if v.id == vessel_id]

    if port_id is not None:
        ports = [p for p in ports if p.id == port_id]

    options = []
    weather_cache = {}
    forecast_cache = {}

    for vessel in vessels:
        for port in ports:

            # ---------------------------------------------------------
            # VESSEL-PORT COMPATIBILITY
            # ---------------------------------------------------------

            compatibility = check_port_vessel_compatibility(
                port=port,
                vessel_loa_m=vessel.loa_m,
                vessel_beam_m=vessel.beam_m,
                vessel_draft_m=vessel.draft_m,
            )

            if not compatibility["feasible"]:
                options.append(
                    {
                        "feasible": False,
                        "vessel_id": vessel.id,
                        "port_id": port.id,
                        "rejection_reasons": compatibility["reasons"],
                    }
                )
                continue

            # ---------------------------------------------------------
            # ARRIVAL FEASIBILITY
            #
            # Calculated from actual vessel and port dimensions.
            # Higher score = better clearance.
            # ---------------------------------------------------------

            arrival_feasibility_score = (
                calculate_arrival_feasibility_score(
                    port=port,
                    vessel_loa_m=vessel.loa_m,
                    vessel_beam_m=vessel.beam_m,
                    vessel_draft_m=vessel.draft_m,
                )
            )

            # ---------------------------------------------------------
            # FREIGHT FORECAST
            # ---------------------------------------------------------

            forecast_key = (
                origin_country,
                destination_region,
                cargo_type,
                vessel.vessel_class,
                str(arrival_date),
            )

            if forecast_key not in forecast_cache:
                forecast_cache[forecast_key] = get_freight_forecast(
                    db=db,
                    request=ForecastRequest(
                        origin_country=origin_country,
                        destination_region=destination_region,
                        cargo_type=cargo_type,
                        vessel_class=vessel.vessel_class,
                        forecast_date=arrival_date,
                    ),
                )

            forecast = forecast_cache[forecast_key]

            if forecast["forecast_rate"] is None:
                options.append(
                    {
                        "feasible": False,
                        "vessel_id": vessel.id,
                        "port_id": port.id,
                        "freight_rate": None,
                        "total_landed_cost": None,
                        "overall_risk": None,
                        "expected_delay_hours": None,
                        "congestion_score": None,
                        "arrival_feasibility_score": (
                            arrival_feasibility_score
                        ),
                        "forecast": forecast,
                        "cost": None,
                        "risk": None,
                        "rejection_reasons": [
                            forecast.get(
                                "message",
                                "Freight market forecast is unavailable.",
                            )
                        ],
                    }
                )
                continue

            # ---------------------------------------------------------
            # CONGESTION RISK
            # ---------------------------------------------------------

            congestion = calculate_congestion_score(
                port.average_waiting_hours
            )

            delay_hours = estimate_delay_hours(
                port.average_waiting_hours
            )

            # ---------------------------------------------------------
            # WEATHER RISK
            #
            # Uses the selected port's coordinates and arrival date.
            # ---------------------------------------------------------

            weather_key = (
                port.latitude,
                port.longitude,
                str(arrival_date),
            )

            if weather_key not in weather_cache:
                weather_cache[weather_key] = get_weather_risk(
                    latitude=port.latitude,
                    longitude=port.longitude,
                    target_date=arrival_date,
                )

            weather = weather_cache[weather_key]

            weather_score = weather.get(
                "weather_score"
            )

            # ---------------------------------------------------------
            # OVERALL RISK
            # ---------------------------------------------------------

            if weather.get("data_status") == "KNOWN":
                risk_data_status = "KNOWN"
            else:
                risk_data_status = "ESTIMATED"

            risk = calculate_risk(
                congestion_score=congestion["score"],
                weather_score=weather_score,
                data_status=risk_data_status,
            )

            # ---------------------------------------------------------
            # WEATHER DETAILS
            # ---------------------------------------------------------

            risk["weather_details"] = {
                "weather_score": weather.get(
                    "weather_score"
                ),
                "risk_level": weather.get(
                    "risk_level"
                ),
                "wind_speed_kn": weather.get(
                    "wind_speed_kn"
                ),
                "wind_gusts_kn": weather.get(
                    "wind_gusts_kn"
                ),
                "precipitation_mm": weather.get(
                    "precipitation_mm"
                ),
                "precipitation_probability_percent": weather.get(
                    "precipitation_probability_percent"
                ),
                "visibility_m": weather.get(
                    "visibility_m"
                ),
                "weather_codes": weather.get(
                    "weather_codes"
                ),
                "source": weather.get(
                    "source"
                ),
                "data_status": weather.get(
                    "data_status"
                ),
                "message": weather.get(
                    "message"
                ),
            }

            # ---------------------------------------------------------
            # PROTOTYPE COST INPUTS
            #
            # These are explicitly estimated values.
            # They are NOT claimed as live market data.
            # ---------------------------------------------------------

            bunker_cost = PROTOTYPE_BUNKER_COST_USD
            port_cost = PROTOTYPE_PORT_COST_USD
            demurrage_rate_per_day = PROTOTYPE_DEMURRAGE_RATE_USD_PER_DAY

            cost = calculate_cost(
                quantity_tonnes=quantity_tonnes,
                freight_rate=forecast["forecast_rate"],
                bunker_cost=bunker_cost,
                port_cost=port_cost,
                expected_delay_hours=delay_hours,
                demurrage_rate_per_day=demurrage_rate_per_day,
                freight_rate_unit=forecast.get(
                    "unit",
                    "USD/day",
                ),
                voyage_duration_days=charter_duration_days,
            )

            # ---------------------------------------------------------
            # COST VALIDATION
            # ---------------------------------------------------------

            if cost["total_landed_cost"] is None:
                reason = (
                    "Voyage duration is required to convert the "
                    "USD/day market freight benchmark into freight cost."
                    if charter_duration_days is None
                    else
                    "Required cost inputs are unavailable; total "
                    "landed cost cannot be calculated reliably."
                )

                options.append(
                    {
                        "feasible": False,
                        "vessel_id": vessel.id,
                        "port_id": port.id,
                        "freight_rate": forecast["forecast_rate"],
                        "total_landed_cost": None,
                        "overall_risk": risk["overall_risk"],
                        "expected_delay_hours": delay_hours,
                        "congestion_score": (
                            congestion["score"]
                        ),
                        "arrival_feasibility_score": (
                            arrival_feasibility_score
                        ),
                        "forecast": forecast,
                        "cost": cost,
                        "risk": risk,
                        "rejection_reasons": [
                            reason
                        ],
                    }
                )
                continue

            # ---------------------------------------------------------
            # FEASIBLE OPTION
            # ---------------------------------------------------------

            options.append(
                {
                    "feasible": True,
                    "vessel_id": vessel.id,
                    "port_id": port.id,
                    "vessel_class": vessel.vessel_class,
                    "freight_rate": forecast["forecast_rate"],
                    "expected_delay_hours": delay_hours,
                    "overall_risk": risk["overall_risk"],
                    "congestion_score": (
                        congestion["score"]
                    ),
                    "arrival_feasibility_score": (
                        arrival_feasibility_score
                    ),
                    "total_landed_cost": (
                        cost["total_landed_cost"]
                    ),
                    "forecast": forecast,
                    "cost": cost,
                    "risk": risk,
                    "rejection_reasons": [],
                }
            )

    return generate_recommendation(
        options=options
    )