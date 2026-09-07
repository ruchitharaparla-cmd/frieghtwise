from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.decision_engine_service import run_decision_engine


router = APIRouter(tags=["Recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
)
def recommend(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    return run_decision_engine(
        db=db,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
        origin_country=request.origin_country,
        destination_region=request.destination_region,
        arrival_date=request.arrival_date,
    )