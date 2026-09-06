from sqlalchemy import Column, Float, Integer, String

from app.core.database import Base


class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    code = Column(String(20), nullable=True)

    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, default="India")

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    max_draft_m = Column(Float, nullable=True)
    max_loa_m = Column(Float, nullable=True)
    max_beam_m = Column(Float, nullable=True)

    annual_capacity_tonnes = Column(Float, nullable=True)
    utilization_percent = Column(Float, nullable=True)
    average_waiting_hours = Column(Float, nullable=True)

    cargo_types = Column(String(500), nullable=True)

    data_status = Column(String(20), default="KNOWN", nullable=False)
    source = Column(String(255), nullable=True)