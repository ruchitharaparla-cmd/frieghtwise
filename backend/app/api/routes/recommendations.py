from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.ai_service import FreightWiseAIService
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
    # ---------------------------------------------------------
    # 1. Run the authoritative numerical decision engine.
    # ---------------------------------------------------------
    recommendation = run_decision_engine(
        db=db,
        cargo_type=request.cargo_type,
        quantity_tonnes=request.quantity_tonnes,
        origin_country=request.origin_country,
        destination_region=request.destination_region,
        arrival_date=request.arrival_date,
        charter_duration_days=request.charter_duration_days,
    )

    # ---------------------------------------------------------
    # 2. Stage 7 AI/RAG explanation layer.
    #
    # The AI does NOT make or modify the recommendation.
    # It only explains the authoritative pipeline outputs.
    # ---------------------------------------------------------
    ai_service = FreightWiseAIService()

    ai_analysis = ai_service.explain_recommendation(
        recommendation=recommendation,
        voyage={
            "cargo_type": request.cargo_type,
            "quantity_tonnes": request.quantity_tonnes,
            "origin_country": request.origin_country,
            "destination_region": request.destination_region,
            "arrival_date": request.arrival_date,
            "charter_duration_days": request.charter_duration_days,
        },
        forecast=recommendation.get("forecast"),
        cost=recommendation.get("cost"),
        risk=recommendation.get("risk"),
    )

    # MarketAnalysisResponse is a dataclass with to_dict().
    if hasattr(ai_analysis, "to_dict"):
        ai_analysis = ai_analysis.to_dict()

    # ---------------------------------------------------------
    # 3. Attach AI explanation without changing the decision.
    # ---------------------------------------------------------
    recommendation["ai_analysis"] = ai_analysis

    return recommendation
