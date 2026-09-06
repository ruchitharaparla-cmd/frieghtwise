"""
Common Metrics Module for FreightWise Round 2 — Stage 2 Freight Forecasting.
Provides standardized calculation of MAE, RMSE, and MAPE metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, Union, Sequence


def _to_numpy_array(data: Union[Sequence, pd.Series, np.ndarray]) -> np.ndarray:
    """Helper to convert input array-like structures to 1D float numpy arrays."""
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 1:
        arr = arr.ravel()
    return arr


def calculate_mae(
    y_true: Union[Sequence, pd.Series, np.ndarray],
    y_pred: Union[Sequence, pd.Series, np.ndarray],
) -> float:
    """
    Calculates Mean Absolute Error (MAE).
    MAE = (1 / n) * sum(|y_true - y_pred|)
    """
    y_t = _to_numpy_array(y_true)
    y_p = _to_numpy_array(y_pred)

    if len(y_t) == 0 or len(y_p) == 0:
        raise ValueError("Inputs for MAE calculation cannot be empty.")
    if len(y_t) != len(y_p):
        raise ValueError(f"Shape mismatch: y_true length {len(y_t)} != y_pred length {len(y_p)}.")

    return float(np.mean(np.abs(y_t - y_p)))


def calculate_rmse(
    y_true: Union[Sequence, pd.Series, np.ndarray],
    y_pred: Union[Sequence, pd.Series, np.ndarray],
) -> float:
    """
    Calculates Root Mean Squared Error (RMSE).
    RMSE = sqrt((1 / n) * sum((y_true - y_pred)^2))
    """
    y_t = _to_numpy_array(y_true)
    y_p = _to_numpy_array(y_pred)

    if len(y_t) == 0 or len(y_p) == 0:
        raise ValueError("Inputs for RMSE calculation cannot be empty.")
    if len(y_t) != len(y_p):
        raise ValueError(f"Shape mismatch: y_true length {len(y_t)} != y_pred length {len(y_p)}.")

    return float(np.sqrt(np.mean((y_t - y_p) ** 2)))


def calculate_mape(
    y_true: Union[Sequence, pd.Series, np.ndarray],
    y_pred: Union[Sequence, pd.Series, np.ndarray],
    epsilon: float = 1e-8,
) -> float:
    """
    Calculates Mean Absolute Percentage Error (MAPE) as a percentage float.
    MAPE (%) = (100 / n) * sum(|y_true - y_pred| / max(|y_true|, epsilon))
    """
    y_t = _to_numpy_array(y_true)
    y_p = _to_numpy_array(y_pred)

    if len(y_t) == 0 or len(y_p) == 0:
        raise ValueError("Inputs for MAPE calculation cannot be empty.")
    if len(y_t) != len(y_p):
        raise ValueError(f"Shape mismatch: y_true length {len(y_t)} != y_pred length {len(y_p)}.")

    denominator = np.where(np.abs(y_t) < epsilon, epsilon, np.abs(y_t))
    mape = np.mean(np.abs((y_t - y_p) / denominator)) * 100.0
    return float(mape)


def calculate_all_metrics(
    y_true: Union[Sequence, pd.Series, np.ndarray],
    y_pred: Union[Sequence, pd.Series, np.ndarray],
) -> Dict[str, float]:
    """
    Calculates MAE, RMSE, and MAPE in a single call.
    Returns dictionary with keys 'MAE', 'RMSE', 'MAPE'.
    """
    return {
        "MAE": calculate_mae(y_true, y_pred),
        "RMSE": calculate_rmse(y_true, y_pred),
        "MAPE": calculate_mape(y_true, y_pred),
    }
