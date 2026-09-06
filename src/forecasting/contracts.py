"""
Forecasting Dataset and Evaluation Contracts for FreightWise Round 2 — Stage 2.
Enforces schema validation, chronological ordering, target integrity,
and strict separation between the exact 26-feature XGBoost contract
and the broader 46-feature freight dataset.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# Exact 26 feature contract used by Round 1 final XGBoost model
XGBOOST_26_FEATURES: List[str] = [
    "freight_lag_1",
    "freight_lag_3",
    "freight_lag_6",
    "freight_lag_12",
    "freight_rolling_mean_3",
    "freight_rolling_mean_6",
    "freight_rolling_mean_12",
    "freight_rolling_std_3",
    "baltic_dry_index_lag_1",
    "baltic_dry_index_lag_3",
    "brent_price_lag_1",
    "brent_price_lag_3",
    "wti_price_lag_1",
    "wti_price_lag_3",
    "dxy_index_lag_1",
    "dxy_index_lag_3",
    "vix_lag_1",
    "vix_lag_3",
    "gpr_index_lag_1",
    "gpr_index_lag_3",
    "thermal_coal_price_lag_1",
    "thermal_coal_price_lag_3",
    "month_num",
    "quarter",
    "month_sin",
    "month_cos",
]

DEFAULT_TARGET_COL: str = "bulk_carrier_handysize_usd_day"
DEFAULT_DATE_COL: str = "date"


class ForecastingDatasetContract:
    """
    Contract validator for time-series freight forecasting datasets.
    """

    @staticmethod
    def validate(
        df: pd.DataFrame,
        target_col: str = DEFAULT_TARGET_COL,
        date_col: str = DEFAULT_DATE_COL,
        require_xgboost_features: bool = False,
    ) -> bool:
        """
        Validates structure, sorting, nulls, and schema contract of a forecasting DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}")

        if df.empty:
            raise ValueError("Forecasting DataFrame cannot be empty.")

        if date_col not in df.columns:
            raise ValueError(f"Missing required date column '{date_col}' in dataset.")

        if target_col not in df.columns:
            raise ValueError(f"Missing required target column '{target_col}' in dataset.")

        # Null target check
        if df[target_col].isnull().any():
            raise ValueError(f"Target column '{target_col}' contains null values.")

        # Chronological ordering check
        dates = pd.to_datetime(df[date_col])
        if not dates.is_monotonic_increasing:
            raise ValueError(f"Dataset is not chronologically sorted by '{date_col}'.")

        # Optional XGBoost feature contract check
        if require_xgboost_features:
            missing = [f for f in XGBOOST_26_FEATURES if f not in df.columns]
            if missing:
                raise ValueError(f"Dataset is missing XGBoost feature contract columns: {missing}")

        return True

    @staticmethod
    def extract_xgboost_features(
        df: pd.DataFrame,
        feature_list: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Extracts and isolates exact 26 XGBoost model features from broader dataset.
        Returns a clean, ordered copy of the 26 features.
        """
        target_features = feature_list or XGBOOST_26_FEATURES
        missing = [f for f in target_features if f not in df.columns]
        if missing:
            raise KeyError(f"DataFrame is missing required model input features: {missing}")

        return df[target_features].copy()


@dataclass
class EvaluationResultContract:
    """
    Contract for standardized model evaluation output.
    """

    model_name: str
    split_name: str
    sample_size: int
    metrics: Dict[str, float]

    def validate(self) -> bool:
        if not self.model_name:
            raise ValueError("model_name cannot be empty.")
        if not self.split_name:
            raise ValueError("split_name cannot be empty.")
        if self.sample_size <= 0:
            raise ValueError(f"sample_size must be positive, got {self.sample_size}.")
        required_metrics = {"MAE", "RMSE", "MAPE"}
        missing_metrics = required_metrics - set(self.metrics.keys())
        if missing_metrics:
            raise ValueError(f"Evaluation metrics missing required fields: {missing_metrics}")
        return True

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "model_name": self.model_name,
            "split_name": self.split_name,
            "sample_size": self.sample_size,
            "metrics": self.metrics,
        }
