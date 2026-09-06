"""
FreightWise Stage 2 — Freight Forecasting Package.
Exposes dataset contracts, chronological split utilities, and metric evaluation routines.
"""

from .contracts import (
    ForecastingDatasetContract,
    EvaluationResultContract,
    XGBOOST_26_FEATURES,
)
from .split import (
    TimeSeriesSplitResult,
    chronological_train_val_test_split,
)
from .metrics import (
    calculate_mae,
    calculate_rmse,
    calculate_mape,
    calculate_all_metrics,
)

__all__ = [
    "ForecastingDatasetContract",
    "EvaluationResultContract",
    "XGBOOST_26_FEATURES",
    "TimeSeriesSplitResult",
    "chronological_train_val_test_split",
    "calculate_mae",
    "calculate_rmse",
    "calculate_mape",
    "calculate_all_metrics",
]
