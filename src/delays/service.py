"""
Production Service Layer for FreightWise Stage 3 — Delay & Congestion Prediction.

Exposes stable inference APIs for downstream modules:
- VesselTurnaroundService: Predicts vessel turnaround hours and delay risk score.
- PortCongestionService: Predicts 1-week-ahead global port congestion index and high-risk status.
  Enforces India Port Data Absence Guard (Correction 4: raises IndiaPortDataAbsentError on Indian ports).
"""

import hashlib
import os
from typing import Any, Dict, List, Mapping, Optional, Union
import numpy as np
import pandas as pd
import joblib

from .contracts import (
    DELAY_RISK_THRESHOLD_HOURS,
    HIGH_CONGESTION_THRESHOLD_INDEX,
    PORT_CONGESTION_FEATURES,
    VESSEL_FEATURES_12,
    PortCongestionContract,
)
from .vessel_turnaround import (
    VESSEL_DELAY_RISK_MODEL_PATH,
    VESSEL_TURNAROUND_MODEL_PATH,
)
from .port_congestion import (
    PORT_CONGESTION_CLASSIFIER_PATH,
    PORT_CONGESTION_REGRESSOR_PATH,
)


class IndiaPortDataAbsentError(ValueError):
    """Raised when an Indian port prediction is requested from global-only dataset."""
    pass


def compute_model_hash(filepath: str) -> str:
    """Computes SHA-256 hash of a model file."""
    if not os.path.exists(filepath):
        return "UNKNOWN_HASH"
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class VesselTurnaroundService:
    """
    Production inference service wrapping Stage 3 vessel turnaround and delay risk models.
    """

    def __init__(
        self,
        turnaround_model_path: Optional[str] = None,
        delay_risk_model_path: Optional[str] = None,
        auto_load: bool = True,
    ) -> None:
        self.turnaround_path: str = turnaround_model_path or VESSEL_TURNAROUND_MODEL_PATH
        self.delay_risk_path: str = delay_risk_model_path or VESSEL_DELAY_RISK_MODEL_PATH
        self.reg_model: Optional[Any] = None
        self.clf_model: Optional[Any] = None
        self.model_version: Optional[str] = None

        if auto_load:
            self.load_models()

    def load_models(self) -> None:
        """Loads regression and classification pipelines into memory."""
        if not os.path.exists(self.turnaround_path):
            raise FileNotFoundError(f"Vessel turnaround model not found at {self.turnaround_path}")
        if not os.path.exists(self.delay_risk_path):
            raise FileNotFoundError(f"Vessel delay risk model not found at {self.delay_risk_path}")

        self.reg_model = joblib.load(self.turnaround_path)
        self.clf_model = joblib.load(self.delay_risk_path)
        self.model_version = compute_model_hash(self.turnaround_path)[:16]

    def predict_turnaround(
        self,
        input_data: Union[Mapping[str, Any], pd.DataFrame, pd.Series],
    ) -> Dict[str, Any]:
        """
        Predicts turnaround hours and delay risk for a single vessel voyage.
        """
        if self.reg_model is None or self.clf_model is None:
            self.load_models()

        if isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        elif isinstance(input_data, pd.Series):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, (dict, Mapping)):
            df = pd.DataFrame([dict(input_data)])
        else:
            raise TypeError(f"Unsupported input type '{type(input_data).__name__}'")

        if len(df) != 1:
            raise ValueError(f"predict_turnaround() expects 1 row, got {len(df)}")

        # Validate feature contract
        missing = [f for f in VESSEL_FEATURES_12 if f not in df.columns]
        if missing:
            raise ValueError(f"Missing required vessel feature(s): {missing}")

        X = df[VESSEL_FEATURES_12].copy()

        # Handle categoricals
        for col in ["route_type", "engine_type", "maintenance_status", "weather_condition"]:
            X[col] = X[col].fillna("Unknown").astype(str)

        # Inference
        pred_hours = float(self.reg_model.predict(X)[0])
        pred_prob = float(self.clf_model.predict_proba(X)[0, 1]) if hasattr(self.clf_model, "predict_proba") else float(self.clf_model.predict(X)[0])
        risk_level = "High" if pred_hours > DELAY_RISK_THRESHOLD_HOURS or pred_prob >= 0.5 else "Low"

        date_val = str(df["date"].iloc[0]) if "date" in df.columns else "N/A"

        return {
            "model_name": "Vessel Turnaround & Delay Risk Model",
            "model_version": self.model_version,
            "forecast_date": date_val,
            "predicted_turnaround_hours": round(pred_hours, 2),
            "delay_risk_score": round(pred_prob, 4),
            "delay_risk_level": risk_level,
            "unit": "hours",
        }


class PortCongestionService:
    """
    Production inference service wrapping Stage 3 Global Port Congestion regressor and classifier artifacts.
    Enforces Correction 4: Raises IndiaPortDataAbsentError on Indian port queries and never returns numeric predictions for Indian ports.
    """

    def __init__(
        self,
        regressor_path: Optional[str] = None,
        classifier_path: Optional[str] = None,
        auto_load: bool = True,
    ) -> None:
        self.regressor_path: str = regressor_path or PORT_CONGESTION_REGRESSOR_PATH
        self.classifier_path: str = classifier_path or PORT_CONGESTION_CLASSIFIER_PATH
        self.reg_model: Optional[Any] = None
        self.clf_model: Optional[Any] = None
        self.model_version: Optional[str] = None

        if auto_load:
            self.load_models()

    def load_models(self) -> None:
        """Loads port congestion regressor and classifier artifacts into memory."""
        if not os.path.exists(self.regressor_path):
            raise FileNotFoundError(f"Port congestion regressor not found at {self.regressor_path}")
        if not os.path.exists(self.classifier_path):
            raise FileNotFoundError(f"Port congestion classifier not found at {self.classifier_path}")

        self.reg_model = joblib.load(self.regressor_path)
        self.clf_model = joblib.load(self.classifier_path)
        self.model_version = compute_model_hash(self.classifier_path)[:16]

    def _check_india_port(self, port_name: str) -> None:
        """Correction 4: Raises IndiaPortDataAbsentError if port is an Indian port."""
        india_keywords = [
            "india", "visakhapatnam", "paradip", "dhamra", "gangavaram",
            "krishnapatnam", "haldia", "mumbai", "jnpt", "chennai", "kandla", "cochin"
        ]
        if any(kw in str(port_name).lower() for kw in india_keywords):
            raise IndiaPortDataAbsentError(
                f"Port '{port_name}' is an Indian port. Current port congestion dataset contains "
                "ZERO Indian ports. Numeric global proxy predictions are strictly blocked for Indian ports. "
                "Model is scoped exclusively to GLOBAL_CONGESTION_RISK."
            )

    def predict_congestion(
        self,
        input_data: Union[Mapping[str, Any], pd.DataFrame, pd.Series],
    ) -> Dict[str, Any]:
        """
        Predicts 1-week-ahead congestion index and high-risk status for a global port.
        """
        if self.reg_model is None or self.clf_model is None:
            self.load_models()

        if isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        elif isinstance(input_data, pd.Series):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, (dict, Mapping)):
            df = pd.DataFrame([dict(input_data)])
        else:
            raise TypeError(f"Unsupported input type '{type(input_data).__name__}'")

        if len(df) != 1:
            raise ValueError(f"predict_congestion() expects 1 row, got {len(df)}")

        port_val = str(df["port"].iloc[0]) if "port" in df.columns else "Unknown"

        # Correction 4: Check Indian port and raise error BEFORE any feature validation or numeric prediction
        self._check_india_port(port_val)

        missing = [f for f in PORT_CONGESTION_FEATURES if f not in df.columns]
        if missing:
            raise ValueError(f"Missing required port congestion feature(s): {missing}")

        X = df[PORT_CONGESTION_FEATURES].copy()

        # Inference
        pred_index = float(self.reg_model.predict(X)[0]) if hasattr(self.reg_model, "predict") else float(X["congestion_index"].iloc[0])
        pred_label = int(self.clf_model.predict(X)[0]) if hasattr(self.clf_model, "predict") else int(pred_index >= HIGH_CONGESTION_THRESHOLD_INDEX)
        pred_prob = float(self.clf_model.predict_proba(X)[0, 1]) if hasattr(self.clf_model, "predict_proba") else float(pred_label)

        week_val = str(df["week_start"].iloc[0]) if "week_start" in df.columns else "N/A"

        return {
            "model_name": "Global Port Congestion Risk Model",
            "model_version": self.model_version,
            "port": port_val,
            "forecast_week": week_val,
            "predicted_congestion_index": round(pred_index, 4),
            "high_congestion_risk": bool(pred_label == 1),
            "risk_probability": round(pred_prob, 4),
            "data_scope": "GLOBAL_CONGESTION_RISK",
        }
