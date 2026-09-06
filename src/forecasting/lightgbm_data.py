"""
LightGBM Dataset Preparation Module for FreightWise Round 2 — Stage 2.2A.
Provides dynamic feature schema derivation, temporal leakage audit, target separation,
and chronological train/validation/test dataset preparation for LightGBM.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .contracts import ForecastingDatasetContract, DEFAULT_TARGET_COL, DEFAULT_DATE_COL
from .split import chronological_train_val_test_split, TimeSeriesSplitResult


# Metadata and target columns to explicitly exclude from LightGBM feature matrix X
EXCLUDED_METADATA_COLUMNS: List[str] = [
    "date",
    "year_month",
    "canonical_month_start",
    DEFAULT_TARGET_COL,
]


def audit_temporal_leakage(feature_name: str) -> bool:
    """
    Audits a feature name for potential temporal leakage.
    Target-derived lag and rolling features are allowed only if they use
    past observations relative to prediction timestamp t.
    Future target lookaheads or future rolling windows are prohibited.
    """
    fname = feature_name.lower()

    # Prohibited future indicators
    prohibited_keywords = ["lead", "future", "next", "shift_-", "target_t_plus"]
    for kw in prohibited_keywords:
        if kw in fname:
            return False

    return True


def derive_lightgbm_feature_contract(df: pd.DataFrame) -> List[str]:
    """
    Dynamically inspects DataFrame schema and derives the approved LightGBM feature contract.

    Rules:
      1. Excludes date/time metadata columns ('date', 'year_month', 'canonical_month_start').
      2. Excludes target column ('bulk_carrier_handysize_usd_day').
      3. Excludes non-numeric columns.
      4. Audits features for temporal leakage.
      5. Returns deterministic, ordered list of approved feature names.
    """
    candidate_cols = [col for col in df.columns if col not in EXCLUDED_METADATA_COLUMNS]

    approved_features: List[str] = []
    for col in candidate_cols:
        # Check numeric data type
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        # Audit temporal leakage
        if not audit_temporal_leakage(col):
            continue

        approved_features.append(col)

    # Sort deterministically if necessary, or preserve natural dataset schema order
    return approved_features


# Explicit static feature contract list derived from freight_model_features.csv schema (43 features)
LIGHTGBM_FEATURES: List[str] = [
    "baltic_dry_index",
    "tanker_rate_aframax_usd_day",
    "supply_chain_pressure_index",
    "on_time_delivery_pct",
    "bdi_mom_change_pct",
    "container_yoy_pct",
    "brent_price",
    "wti_price",
    "dxy_index",
    "vix",
    "gpr_index",
    "brent_volatility_30d",
    "wti_volatility_30d",
    "brent_wti_spread",
    "event_severity",
    "event_flag",
    "thermal_coal_price",
    "freight_lag_1",
    "freight_lag_3",
    "freight_lag_6",
    "freight_lag_12",
    "freight_rolling_mean_3",
    "freight_rolling_mean_6",
    "freight_rolling_mean_12",
    "freight_rolling_std_3",
    "month_num",
    "quarter",
    "month_sin",
    "month_cos",
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
]


@dataclass
class LightGBMSplitResult:
    """
    Container for LightGBM split datasets: (X_train, y_train), (X_val, y_val), (X_test, y_test).
    """

    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series
    feature_names: List[str]
    train_dates: pd.Series
    val_dates: pd.Series
    test_dates: pd.Series

    @property
    def shapes(self) -> Dict[str, Tuple[Tuple[int, int], Tuple[int,]]]:
        return {
            "train": (self.X_train.shape, self.y_train.shape),
            "val": (self.X_val.shape, self.y_val.shape),
            "test": (self.X_test.shape, self.y_test.shape),
        }

    def verify_no_leakage(self, target_col: str = DEFAULT_TARGET_COL) -> bool:
        """
        Verifies zero feature/target leakage and strict chronological separation.
        """
        # 1. Target non-presence in feature matrices
        for split_name, X_df in [("train", self.X_train), ("val", self.X_val), ("test", self.X_test)]:
            if target_col in X_df.columns:
                raise ValueError(f"Target column '{target_col}' detected inside feature matrix X_{split_name}!")
            for meta_col in ["date", "year_month", "canonical_month_start"]:
                if meta_col in X_df.columns:
                    raise ValueError(f"Raw date metadata column '{meta_col}' detected inside X_{split_name}!")

        # 2. Date set disjointness & chronological ordering
        t_dates = set(self.train_dates)
        v_dates = set(self.val_dates)
        te_dates = set(self.test_dates)

        if t_dates & v_dates or v_dates & te_dates or t_dates & te_dates:
            raise ValueError("Overlapping dates detected across LightGBM split partitions.")

        t_max = pd.to_datetime(self.train_dates).max()
        v_min = pd.to_datetime(self.val_dates).min()
        v_max = pd.to_datetime(self.val_dates).max()
        te_min = pd.to_datetime(self.test_dates).min()

        if t_max >= v_min:
            raise ValueError(f"Temporal leakage: max train date ({t_max}) >= min validation date ({v_min})")
        if v_max >= te_min:
            raise ValueError(f"Temporal leakage: max validation date ({v_max}) >= min test date ({te_min})")

        return True


class LightGBMDatasetPreparer:
    """
    Prepares LightGBM datasets from time-series feature DataFrames.
    """

    def __init__(self, feature_list: Optional[List[str]] = None):
        self.feature_list = feature_list or LIGHTGBM_FEATURES

    def prepare(
        self,
        df: pd.DataFrame,
        target_col: str = DEFAULT_TARGET_COL,
        date_col: str = DEFAULT_DATE_COL,
        train_size: int = 143,
        val_size: int = 12,
        test_size: int = 12,
    ) -> LightGBMSplitResult:
        """
        Validates, prepares feature matrix X and target y, and splits chronologically.
        """
        # Validate dataset structure
        ForecastingDatasetContract.validate(df, target_col=target_col, date_col=date_col)

        # Derive & verify feature contract
        derived_features = derive_lightgbm_feature_contract(df)

        # Ensure requested features are present in dataset
        missing = [f for f in self.feature_list if f not in df.columns]
        if missing:
            raise KeyError(f"DataFrame is missing required LightGBM feature columns: {missing}")

        # Check numeric data types across all features
        for f in self.feature_list:
            if not pd.api.types.is_numeric_dtype(df[f]):
                raise TypeError(f"Feature '{f}' is not numeric!")

        # Check for missing values in features
        null_counts = df[self.feature_list].isnull().sum()
        if null_counts.sum() > 0:
            null_cols = null_counts[null_counts > 0].to_dict()
            raise ValueError(f"Null values detected in LightGBM feature matrix: {null_cols}")

        # Chronological split using Stage 2.1 split utility
        split_res: TimeSeriesSplitResult = chronological_train_val_test_split(
            df,
            date_col=date_col,
            train_size=train_size,
            val_size=val_size,
            test_size=test_size,
        )

        # Extract X and y for train, validation, test
        X_train = split_res.train[self.feature_list].copy()
        y_train = split_res.train[target_col].copy()

        X_val = split_res.validation[self.feature_list].copy()
        y_val = split_res.validation[target_col].copy()

        X_test = split_res.test[self.feature_list].copy()
        y_test = split_res.test[target_col].copy()

        result = LightGBMSplitResult(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            feature_names=list(self.feature_list),
            train_dates=split_res.train[date_col].copy(),
            val_dates=split_res.validation[date_col].copy(),
            test_dates=split_res.test[date_col].copy(),
        )

        result.verify_no_leakage(target_col=target_col)
        return result


def prepare_lightgbm_datasets(loader: Optional[Any] = None) -> LightGBMSplitResult:
    """
    Helper function that loads freight_model_features.csv via Stage 1 DataLoader
    and returns prepared LightGBMSplitResult.
    """
    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()

    df = loader.load_freight_model_features()
    preparer = LightGBMDatasetPreparer()
    return preparer.prepare(df)
