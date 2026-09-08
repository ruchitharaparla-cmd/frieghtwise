from app.schemas.forecast import ForecastRequest
from app.ml.forecasting.predict import predict_freight


def get_freight_forecast(
    db,
    request: ForecastRequest,
):
    result = predict_freight(
        forecast_date=request.forecast_date,
    )

    return result
