from sqlalchemy import Column, Date, Float, Integer, String

from app.core.database import Base


class Freight(Base):
    __tablename__ = "freight_rates"

    id = Column(Integer, primary_key=True, index=True)

    origin_country = Column(String(100), nullable=False)
    destination_region = Column(String(100), nullable=False)

    cargo_type = Column(String(100), nullable=False)
    vessel_class = Column(String(50), nullable=False)

    forecast_date = Column(Date, nullable=False)

    freight_rate = Column(Float, nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    unit = Column(String(50), default="per_metric_tonne", nullable=False)

    model_version = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)

    data_status = Column(String(20), default="UNAVAILABLE", nullable=False)
    source = Column(String(255), nullable=True)
