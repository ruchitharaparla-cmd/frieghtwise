from fastapi import APIRouter

from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import generate_recommendation

router = APIRouter(tags=["Recommendations"])


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
)
def recommend(
    request: RecommendationRequest,
):
    return generate_recommendation(
        options=[],
    )