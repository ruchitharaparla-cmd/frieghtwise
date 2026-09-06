"""
Validation Module for FreightWise Stage 2.4 — Freight Forecasting Production/Inference Layer.

Provides rigorous validation for model input features and date tracking.
Ensures:
- All required 26 features are present (extra columns allowed and ignored).
- Columns are ordered strictly according to model.feature_names_in_.
- Features contain exclusively valid numeric data with zero nulls/NaNs.
- Date column is validated separately, strictly maintained, and never passed into the model.
"""

from typing import List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .contracts import DEFAULT_DATE_COL, XGBOOST_26_FEATURES


def validate_date_column(
    df: pd.DataFrame,
    date_col: str = DEFAULT_DATE_COL,
) -> pd.Series:
    """
    Validates the presence, non-emptiness, and validity of the date column.
    The date column is handled separately from model features and is never passed
    to XGBoost.

    Parameters
    ----------
    df : pd.DataFrame
        Input data containing the date column.
    date_col : str
        Name of the date column, default 'date'.

    Returns
    -------
    pd.Series
        Series of ISO-formatted date strings (YYYY-MM-DD) aligned row-by-row.

    Raises
    -------
    ValueError
        If the date column is missing, contains nulls, or has unparseable dates.
    """
    if date_col not in df.columns:
        raise ValueError(
            f"Input is missing mandatory date column '{date_col}'. "
            "A date column is required for forecast tracking."
        )

    date_series = df[date_col]
    if date_series.isnull().any():
        null_indices = date_series[date_series.isnull()].index.tolist()
        raise ValueError(
            f"Date column '{date_col}' contains null/missing values at index: {null_indices}."
        )

    try:
        parsed_dates = pd.to_datetime(date_series)
    except Exception as exc:
        raise ValueError(
            f"Date column '{date_col}' contains unparseable date values: {exc}"
        ) from exc

    # Return standardized ISO formatted date strings
    return parsed_dates.dt.strftime("%Y-%m-%d")


def validate_features(
    df: pd.DataFrame,
    expected_features: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Validates that the input DataFrame contains all 26 required XGBoost features,
    contains zero nulls, contains strictly numeric values, and extracts them in the
    exact ordering specified by expected_features (or XGBOOST_26_FEATURES).

    Extra columns in `df` (such as 'date', target, or metadata) are permitted
    and ignored during feature extraction.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame to validate.
    expected_features : Optional[List[str]]
        The list of feature names in the exact required order (typically model.feature_names_in_).
        If None, defaults to contracts.XGBOOST_26_FEATURES.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing strictly the 26 features ordered exactly by expected_features.

    Raises
    -------
    TypeError
        If df is not a pandas DataFrame.
    ValueError
        If df is empty, missing required features, contains nulls, or contains non-numeric values.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        raise ValueError("Input DataFrame is empty. At least one row is required for inference.")

    features = (
        [str(f) for f in expected_features]
        if expected_features is not None
        else list(XGBOOST_26_FEATURES)
    )

    # 1. Missing features check
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(
            f"Input DataFrame is missing required XGBoost feature(s): {missing}. "
            f"Required {len(features)} features, found {len(set(features).intersection(df.columns))}."
        )

    # 2. Extract in the exact required order (handles shuffled input columns and drops extra columns)
    extracted = df[features].copy()

    # 3. Check for missing/null values (do not silently fill)
    null_cols = extracted.columns[extracted.isnull().any()].tolist()
    if null_cols:
        null_counts = extracted[null_cols].isnull().sum().to_dict()
        raise ValueError(
            f"Input features contain missing/null values in columns: {null_counts}. "
            "Silent imputation is disabled; all required features must have valid values."
        )

    # 4. Check for strictly numeric values
    for col in features:
        # Check dtype or coerce
        series = extracted[col]
        if not pd.api.types.is_numeric_dtype(series):
            # Check if values can be converted to float
            try:
                extracted[col] = pd.to_numeric(series, errors="raise")
            except Exception as exc:
                raise ValueError(
                    f"Feature '{col}' contains non-numeric values: {exc}"
                ) from exc

    return extracted
