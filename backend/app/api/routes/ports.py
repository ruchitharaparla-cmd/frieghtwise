from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.port import PortListResponse
from app.services.port_service import get_ports

router = APIRouter(tags=["Ports"])


@router.get("/ports", response_model=PortListResponse)
def list_ports(
    region: Optional[str] = Query(default=None),
    cargo_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    ports = get_ports(
        db=db,
        region=region,
        cargo_type=cargo_type,
    )

    return {"ports": ports}