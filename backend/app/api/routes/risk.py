from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.port_service import get_port_by_id
from app.services.vessel_service import get_vessel_by_id
from app.services.congestion_service import (
    calculate_congestion_score,
    estimate_delay_hours,
)
from app.services.risk_service import calculate_risk
from app.integrations.weather import get_weather_risk


router = APIRouter(tags=["Risk"])


class RiskRequest(BaseModel):
    port_id: int
    arrival_date: date
    vessel_id: int


@router.post("/risk")
def calculate_risk_endpoint(
    request: RiskRequest,
    db: Session = Depends(get_db),
):
    port = get_port_by_id(
        db,
        request.port_id,
    )

    vessel = get_vessel_by_id(
        db,
        request.vessel_id,
    )

    if port is None:
        return {
            "overall_risk": None,
            "risk_level": "HIGH",
            "factors": {},
            "data_status": "UNAVAILABLE",
            "reason": f"Port with id {request.port_id} was not found.",
        }

    if vessel is None:
        return {
            "overall_risk": None,
            "risk_level": "HIGH",
            "factors": {},
            "data_status": "UNAVAILABLE",
            "reason": f"Vessel with id {request.vessel_id} was not found.",
        }

    # ---------------------------------------------
    # Congestion risk
    # ---------------------------------------------

    congestion = calculate_congestion_score(
        port.average_waiting_hours
    )

    delay_hours = estimate_delay_hours(
        port.average_waiting_hours
    )

    # ---------------------------------------------
    # Weather risk
    # ---------------------------------------------

    weather = get_weather_risk(
        latitude=port.latitude,
        longitude=port.longitude,
        target_date=request.arrival_date,
    )

    weather_score = weather.get("weather_score")

    # ---------------------------------------------
    # Overall risk
    # ---------------------------------------------

    risk_data_status = "ESTIMATED"

    if weather.get("data_status") == "KNOWN":
        risk_data_status = "KNOWN"

    risk = calculate_risk(
        congestion_score=congestion["score"],
        weather_score=weather_score,
        data_status=risk_data_status,
    )

    result = dict(risk)

    # Add weather details so the frontend can explain
    # why the weather contributed to the risk score.
    result["factors"]["weather"]["details"] = {
        "wind_speed_kn": weather.get("wind_speed_kn"),
        "wind_gusts_kn": weather.get("wind_gusts_kn"),
        "precipitation_mm": weather.get("precipitation_mm"),
        "precipitation_probability_percent": weather.get(
            "precipitation_probability_percent"
        ),
        "visibility_m": weather.get("visibility_m"),
        "weather_codes": weather.get("weather_codes"),
        "source": weather.get("source"),
        "data_status": weather.get("data_status"),
    }

    result["expected_delay_hours"] = delay_hours
    result["port_id"] = port.id
    result["vessel_id"] = vessel.id
    result["arrival_date"] = request.arrival_date

    return result