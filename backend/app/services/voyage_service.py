from sqlalchemy.orm import Session

from app.models.voyage import Voyage
from app.schemas.voyage import VoyageCreate


def create_voyage(
    db: Session,
    voyage_data: VoyageCreate,
):
    voyage = Voyage(
        cargo_type=voyage_data.cargo_type,
        quantity_tonnes=voyage_data.quantity_tonnes,
        origin_country=voyage_data.origin_country,
        destination_region=voyage_data.destination_region,
        arrival_date=voyage_data.arrival_date,
        charter_start_date=voyage_data.charter_start_date,
        charter_end_date=voyage_data.charter_end_date,
        status="PLANNED",
    )

    db.add(voyage)
    db.commit()
    db.refresh(voyage)

    return voyage


def get_voyage_by_id(
    db: Session,
    voyage_id: int,
):
    return (
        db.query(Voyage)
        .filter(Voyage.id == voyage_id)
        .first()
    )


def get_voyages(db: Session):
    return (
        db.query(Voyage)
        .order_by(Voyage.id.desc())
        .all()
    )