"""
FreightWise Stage 2 — Freight Forecasting Package.
Exposes dataset contracts, chronological split utilities, metric evaluation routines,
LightGBM dataset preparation, configuration, and training modules,
and Stage 2.2C model evaluation and selection.
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
from .model_selection import (
    ModelSelectionResult,
    CandidateEvaluation,
    evaluate_all_candidates,
    run_model_selection,
    save_comparison_csv,
    COMPARISON_CSV_PATH,
    CANDIDATE_NAIVE,
    CANDIDATE_XGBOOST,
    CANDIDATE_LIGHTGBM,
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
    # Stage 2.2C — Model Evaluation & Selection
    "ModelSelectionResult",
    "CandidateEvaluation",
    "evaluate_all_candidates",
    "run_model_selection",
    "save_comparison_csv",
    "COMPARISON_CSV_PATH",
    "CANDIDATE_NAIVE",
    "CANDIDATE_XGBOOST",
    "CANDIDATE_LIGHTGBM",
]
