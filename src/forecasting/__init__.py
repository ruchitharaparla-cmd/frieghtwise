"""
FreightWise Stage 2 — Freight Forecasting Package.
Exposes dataset contracts, chronological split utilities, metric evaluation routines,
and LightGBM dataset preparation, configuration, and training modules.
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
from .lightgbm_data import (
    LIGHTGBM_FEATURES,
    derive_lightgbm_feature_contract,
    LightGBMDatasetPreparer,
    LightGBMSplitResult,
    prepare_lightgbm_datasets,
)
from .lightgbm_config import (
    LightGBMModelConfig,
    get_default_lightgbm_config,
)
from .lightgbm_train import (
    train_and_evaluate_lightgbm,
    DEFAULT_LIGHTGBM_MODEL_PATH,
    DEFAULT_PREDICTIONS_PATH,
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
    "LIGHTGBM_FEATURES",
    "derive_lightgbm_feature_contract",
    "LightGBMDatasetPreparer",
    "LightGBMSplitResult",
    "prepare_lightgbm_datasets",
    "LightGBMModelConfig",
    "get_default_lightgbm_config",
    "train_and_evaluate_lightgbm",
    "DEFAULT_LIGHTGBM_MODEL_PATH",
    "DEFAULT_PREDICTIONS_PATH",
]
