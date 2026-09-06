from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecast_service import get_freight_forecast

router = APIRouter(tags=["Forecasts"])


@router.post("/forecast", response_model=ForecastResponse)
def forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db),
):
    return get_freight_forecast(
        db=db,
        request=request,
    )