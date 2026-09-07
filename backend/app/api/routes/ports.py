from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.port import PortListResponse, PortResponse
from app.services.port_service import get_port_by_id, get_ports


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


@router.get("/ports/{port_id}", response_model=PortResponse)
def get_port(
    port_id: int,
    db: Session = Depends(get_db),
):
    port = get_port_by_id(
        db=db,
        port_id=port_id,
    )

    if port is None:
        raise HTTPException(
            status_code=404,
            detail=f"Port with id {port_id} was not found.",
        )

    return port