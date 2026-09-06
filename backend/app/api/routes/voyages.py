from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.voyage import VoyageCreate, VoyageResponse
from app.services.voyage_service import (
    create_voyage,
    get_voyage_by_id,
)

router = APIRouter(tags=["Voyages"])


@router.post("/voyages", response_model=VoyageResponse)
def create_voyage_endpoint(
    voyage_data: VoyageCreate,
    db: Session = Depends(get_db),
):
    return create_voyage(
        db=db,
        voyage_data=voyage_data,
    )


@router.get(
    "/voyages/{voyage_id}",
    response_model=VoyageResponse,
)
def get_voyage(
    voyage_id: int,
    db: Session = Depends(get_db),
):
    voyage = get_voyage_by_id(
        db=db,
        voyage_id=voyage_id,
    )

    if voyage is None:
        raise HTTPException(
            status_code=404,
            detail="Voyage not found",
        )

    return voyage