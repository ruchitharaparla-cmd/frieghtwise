from datetime import date
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_forecast(
    latitude: float,
    longitude: float,
    target_date: date,
) -> dict:
    """
    Fetch hourly weather data for a port/location from Open-Meteo.

    No API key is required for the standard non-commercial
    Open-Meteo endpoint used by the FreightWise prototype.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "wind_speed_10m,"
            "wind_gusts_10m,"
            "precipitation,"
            "precipitation_probability,"
            "visibility,"
            "weather_code"
        ),
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "timezone": "auto",
        "wind_speed_unit": "kn",
    }

    url = f"{OPEN_METEO_URL}?{urlencode(params)}"

    try:
        request = Request(
            url,
            headers={
                "User-Agent": "FreightWise/1.0",
            },
        )

        with urlopen(request, timeout=10) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        hourly = data.get("hourly")

        if not hourly:
            return {
                "data_status": "UNAVAILABLE",
                "source": "Open-Meteo",
                "message": "Open-Meteo returned no hourly weather data.",
            }

        return {
            "data_status": "KNOWN",
            "source": "Open-Meteo",
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "hourly": hourly,
        }

    except Exception as exc:
        return {
            "data_status": "UNAVAILABLE",
            "source": "Open-Meteo",
            "message": f"Weather provider unavailable: {exc}",
        }


def get_weather_risk(
    latitude: float,
    longitude: float,
    target_date: date,
) -> dict:
    """
    Convert Open-Meteo weather data into a FreightWise
    operational weather-risk assessment.

    The weather_score is calculated by FreightWise rules.
    It is NOT a score provided by Open-Meteo.
    """

    weather = get_weather_forecast(
        latitude=latitude,
        longitude=longitude,
        target_date=target_date,
    )

    if weather.get("data_status") != "KNOWN":
        return {
            "weather_score": None,
            "risk_level": "UNKNOWN",
            "data_status": "UNAVAILABLE",
            "source": "Open-Meteo",
            "message": weather.get(
                "message",
                "Weather data unavailable.",
            ),
        }

    hourly = weather["hourly"]

    def maximum(values):
        valid = [
            value for value in values
            if value is not None
        ]
        return max(valid) if valid else None

    def average(values):
        valid = [
            value for value in values
            if value is not None
        ]
        return (
            sum(valid) / len(valid)
            if valid
            else None
        )

    wind_speed = average(
        hourly.get("wind_speed_10m", [])
    )

    wind_gusts = maximum(
        hourly.get("wind_gusts_10m", [])
    )

    precipitation = sum(
        value
        for value in hourly.get("precipitation", [])
        if value is not None
    )

    precipitation_probability = maximum(
        hourly.get(
            "precipitation_probability",
            [],
        )
    )

    visibility = average(
        hourly.get("visibility", [])
    )

    weather_codes = [
        value
        for value in hourly.get("weather_code", [])
        if value is not None
    ]

    # --------------------------------------------------
    # FreightWise weather-risk scoring
    # --------------------------------------------------

    score = 0

    # Wind speed
    if wind_speed is not None:
        if wind_speed >= 30:
            score += 35
        elif wind_speed >= 20:
            score += 20
        elif wind_speed >= 15:
            score += 10

    # Maximum wind gusts
    if wind_gusts is not None:
        if wind_gusts >= 45:
            score += 25
        elif wind_gusts >= 35:
            score += 15
        elif wind_gusts >= 25:
            score += 5

    # Daily precipitation
    if precipitation >= 20:
        score += 20
    elif precipitation >= 10:
        score += 10
    elif precipitation >= 5:
        score += 5

    # Average visibility
    if visibility is not None:
        if visibility < 3000:
            score += 20
        elif visibility < 5000:
            score += 10

    # Keep score within 0-100
    score = min(score, 100)

    # Risk classification
    if score >= 60:
        risk_level = "HIGH"
    elif score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "weather_score": float(score),
        "risk_level": risk_level,
        "wind_speed_kn": wind_speed,
        "wind_gusts_kn": wind_gusts,
        "precipitation_mm": precipitation,
        "precipitation_probability_percent": (
            precipitation_probability
        ),
        "visibility_m": visibility,
        "weather_codes": weather_codes,
        "data_status": "KNOWN",
        "source": "Open-Meteo",
        "message": (
            "Weather risk calculated from Open-Meteo "
            "hourly weather data using FreightWise "
            "risk rules."
        ),
    }