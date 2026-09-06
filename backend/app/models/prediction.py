from sqlalchemy import Column, Date, Float, Integer, String

from app.core.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    prediction_type = Column(String(50), nullable=False)

    origin_country = Column(String(100), nullable=True)
    destination_region = Column(String(100), nullable=True)
    cargo_type = Column(String(100), nullable=True)
    vessel_class = Column(String(50), nullable=True)

    prediction_date = Column(Date, nullable=False)

    predicted_value = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)

    model_version = Column(String(100), nullable=True)

    data_status = Column(String(20), default="UNAVAILABLE", nullable=False)
    source = Column(String(255), nullable=True)