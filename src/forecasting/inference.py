"""
Production Inference Service for FreightWise Stage 2.4 — Freight Forecasting.

Exposes a clean, reusable, stable API for downstream modules
(risk calculation, optimization, procurement, dashboard) to obtain freight rate
forecasts using the production Round 1 XGBoost model.
"""

from typing import Any, Dict, List, Mapping, Optional, Union
import numpy as np
import pandas as pd

from .contracts import DEFAULT_DATE_COL, XGBOOST_26_FEATURES
from .model_loader import (
    DEFAULT_XGBOOST_MODEL_PATH,
    EXPECTED_XGBOOST_SHA256,
    load_xgboost_model,
)
from .validation import validate_date_column, validate_features

CANONICAL_MODEL_NAME: str = "Round 1 XGBoost"
DEFAULT_UNIT: str = "USD/day"


class FreightForecastService:
    """
    Production inference service wrapping the selected Round 1 XGBoost forecasting model.

    Features:
    - Lazy/cached model loading without retraining.
    - Strict validation of 26 feature contract and numeric integrity.
    - Internal reordering of input columns to match model.feature_names_in_.
    - Separation of date tracking from model inputs.
    - Single and batch inference interfaces.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        auto_load: bool = True,
        verify_checksum: bool = True,
    ) -> None:
        """
        Initializes the forecast service.

        Parameters
        ----------
        model_path : Optional[str]
            Path to the XGBoost joblib artifact. Defaults to DEFAULT_XGBOOST_MODEL_PATH.
        auto_load : bool
            Whether to load the model immediately upon instantiation.
        verify_checksum : bool
            Whether to verify SHA-256 artifact integrity against EXPECTED_XGBOOST_SHA256.
        """
        self.model_path: str = model_path or DEFAULT_XGBOOST_MODEL_PATH
        self.model_name: str = CANONICAL_MODEL_NAME
        self.unit: str = DEFAULT_UNIT
        self.verify_checksum: bool = verify_checksum
        self.model: Optional[Any] = None
        self.model_version: Optional[str] = None
        self.feature_names: List[str] = list(XGBOOST_26_FEATURES)

        if auto_load:
            self.load_model()

    def load_model(self) -> None:
        """
        Loads the model artifact into memory and caches its metadata.
        Does not retrain or alter the model artifact.
        """
        self.model, self.model_version = load_xgboost_model(
            model_path=self.model_path,
            verify_checksum=self.verify_checksum,
        )

        if hasattr(self.model, "feature_names_in_"):
            self.feature_names = [str(f) for f in self.model.feature_names_in_]
        else:
            self.feature_names = list(XGBOOST_26_FEATURES)

    def _ensure_loaded(self) -> None:
        """Guards that the model is loaded before inference."""
        if self.model is None:
            self.load_model()

    def predict(
        self,
        input_data: Union[Mapping[str, Any], pd.DataFrame, pd.Series],
        date_col: str = DEFAULT_DATE_COL,
    ) -> Dict[str, Any]:
        """
        Performs a single freight rate prediction.

        Parameters
        ----------
        input_data : Union[Mapping[str, Any], pd.DataFrame, pd.Series]
            Data containing the 26 required features and a mandatory date column.
        date_col : str
            Name of the date column, default 'date'.

        Returns
        -------
        Dict[str, Any] with keys:
            - model_name: str
            - model_version: str (sha256 hash)
            - forecast_date: str (YYYY-MM-DD)
            - predicted_freight_rate: float
            - unit: str ("USD/day")
        """
        self._ensure_loaded()

        # Standardize input into a single-row DataFrame
        if isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        elif isinstance(input_data, pd.Series):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, (dict, Mapping)):
            df = pd.DataFrame([dict(input_data)])
        else:
            raise TypeError(
                f"Unsupported input type '{type(input_data).__name__}'. "
                "Expected dict, pd.Series, or 1-row pd.DataFrame."
            )

        if len(df) != 1:
            raise ValueError(
                f"predict() expects exactly 1 observation, but received {len(df)} rows. "
                "Use predict_batch() for multi-row inference."
            )

        # 1. Validate date separately (never passed into XGBoost)
        forecast_dates = validate_date_column(df, date_col=date_col)
        forecast_date = str(forecast_dates.iloc[0])

        # 2. Validate and reorder features strictly
        X = validate_features(df, expected_features=self.feature_names)

        # 3. Model inference
        raw_pred = self.model.predict(X)
        pred_array = np.asarray(raw_pred).ravel()

        if len(pred_array) != 1:
            raise ValueError(
                f"Model returned {len(pred_array)} predictions for 1 input row."
            )

        predicted_rate = float(pred_array[0])

        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "forecast_date": forecast_date,
            "predicted_freight_rate": predicted_rate,
            "unit": self.unit,
        }

    def predict_batch(
        self,
        df: pd.DataFrame,
        date_col: str = DEFAULT_DATE_COL,
    ) -> pd.DataFrame:
        """
        Performs batch freight rate predictions across multiple rows.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the 26 required features and mandatory date column.
        date_col : str
            Name of the date column, default 'date'.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns:
            ['forecast_date', 'predicted_freight_rate', 'model_name', 'model_version', 'unit']
            corresponding row-by-row to the input.
        """
        self._ensure_loaded()

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

        if df.empty:
            raise ValueError("Input DataFrame is empty for predict_batch().")

        # 1. Validate date separately
        forecast_dates = validate_date_column(df, date_col=date_col)

        # 2. Validate and reorder features strictly
        X = validate_features(df, expected_features=self.feature_names)

        # 3. Batch model inference
        raw_preds = self.model.predict(X)
        pred_array = np.asarray(raw_preds).ravel()

        if len(pred_array) != len(df):
            raise ValueError(
                f"Prediction count mismatch: model returned {len(pred_array)} "
                f"predictions for {len(df)} input rows."
            )

        result_df = pd.DataFrame(
            {
                "forecast_date": forecast_dates.values,
                "predicted_freight_rate": pred_array.astype(float),
                "model_name": self.model_name,
                "model_version": self.model_version,
                "unit": self.unit,
            },
            index=df.index,
        )

        return result_df
