from sqlalchemy import Column, Date, Float, Integer, String

from app.core.database import Base


class Voyage(Base):
    __tablename__ = "voyages"

    id = Column(Integer, primary_key=True, index=True)

    cargo_type = Column(String(100), nullable=False)
    quantity_tonnes = Column(Float, nullable=False)

    origin_country = Column(String(100), nullable=False)
    destination_region = Column(String(100), nullable=False)

    arrival_date = Column(Date, nullable=False)

    charter_start_date = Column(Date, nullable=True)
    charter_end_date = Column(Date, nullable=True)

    status = Column(String(30), default="PLANNED", nullable=False)