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


def run_decision_engine(
    db: Session,
    cargo_type: str,
    quantity_tonnes: float,
    origin_country: str,
    destination_region: str,
    arrival_date,
    charter_duration_days=None,
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
                options.append(
                    {
                        "feasible": False,
                        "vessel_id": vessel.id,
                        "port_id": port.id,
                        "rejection_reasons": compatibility["reasons"],
                    }
                )
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
                        "port_suitability_score": None,
                        "arrival_feasibility_score": None,
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
            # Open-Meteo is an external data source.
            #
            # If weather data is unavailable, the risk engine still
            # works using the available congestion signal.
            # ---------------------------------------------------------

            weather = get_weather_risk(
                latitude=port.latitude,
                longitude=port.longitude,
                target_date=arrival_date,
            )

            weather_score = weather.get("weather_score")

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

            # Attach detailed weather information to the risk result
            # so the recommendation/API can explain the risk.
            risk["weather_details"] = {
                "weather_score": weather.get("weather_score"),
                "risk_level": weather.get("risk_level"),
                "wind_speed_kn": weather.get("wind_speed_kn"),
                "wind_gusts_kn": weather.get("wind_gusts_kn"),
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
                "source": weather.get("source"),
                "data_status": weather.get(
                    "data_status"
                ),
                "message": weather.get("message"),
            }

            # ---------------------------------------------------------
            # DEMO COST INPUTS
            #
            # These remain explicitly estimated prototype values.
            # They are NOT claimed as live market data.
            # ---------------------------------------------------------

            bunker_cost = 300000.0
            port_cost = 100000.0
            demurrage_rate_per_day = 20000.0

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
                        "port_suitability_score": congestion["score"],
                        "arrival_feasibility_score": 0.0,
                        "forecast": forecast,
                        "cost": cost,
                        "risk": risk,
                        "rejection_reasons": [reason],
                    }
                )
                continue

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
                    "arrival_feasibility_score": 0.0,
                    "total_landed_cost": cost["total_landed_cost"],
                    "forecast": forecast,
                    "cost": cost,
                    "risk": risk,
                    "rejection_reasons": [],
                }
            )

    return generate_recommendation(options=options)