from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.freight import Freight
from app.schemas.forecast import ForecastRequest


def get_freight_forecast(
    db: Session,
    request: ForecastRequest,
):
    forecast = (
        db.query(Freight)
        .filter(
            Freight.origin_country == request.origin_country,
            Freight.destination_region == request.destination_region,
            Freight.cargo_type == request.cargo_type,
            Freight.vessel_class == request.vessel_class,
            Freight.forecast_date == request.forecast_date,
        )
        .first()
    )

    if forecast is None:
        return {
            "forecast_rate": None,
            "currency": "USD",
            "unit": "per_metric_tonne",
            "forecast_date": request.forecast_date,
            "model_version": None,
            "confidence": None,
            "data_status": "UNAVAILABLE",
        }

    return {
        "forecast_rate": forecast.freight_rate,
        "currency": forecast.currency,
        "unit": forecast.unit,
        "forecast_date": forecast.forecast_date,
        "model_version": forecast.model_version,
        "confidence": forecast.confidence,
        "data_status": forecast.data_status,
    }