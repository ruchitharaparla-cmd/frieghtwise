from sqlalchemy import Boolean, Column, Float, Integer, String

from app.core.database import Base


class Vessel(Base):
    __tablename__ = "vessels"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    vessel_class = Column(String(50), nullable=False)

    dwt = Column(Float, nullable=True)
    loa_m = Column(Float, nullable=True)
    beam_m = Column(Float, nullable=True)
    draft_m = Column(Float, nullable=True)

    cargo_types = Column(String(500), nullable=True)

    is_available = Column(Boolean, default=True, nullable=False)

    data_status = Column(String(20), default="KNOWN", nullable=False)
    source = Column(String(255), nullable=True)