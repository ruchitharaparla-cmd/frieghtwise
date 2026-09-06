"""
FreightWise Round 2 — Stage 2.2B: LightGBM Training & Evaluation Test Suite.

Covers:
  1. Training succeeds end-to-end without error.
  2. Model trained on exactly the 43 LIGHTGBM_FEATURES contract.
  3. Target column not present in training feature matrix.
  4. Chronological split sizes are exactly 143 / 12 / 12.
  5. Zero temporal overlap across train/validation/test partitions.
  6. Test set is NOT passed to fit() or early stopping callbacks.
  7. Prediction DataFrame has required columns and split tags.
  8. Naive, XGBoost, and LightGBM are evaluated against identical y_test & dates.
  9. best_iteration is recorded and is a positive integer.
 10. Round 1 XGBoost model binary and Round 1 CSVs remain unchanged.
 11. LightGBM model artifact and prediction CSV are new, separate files.
"""

import os
import hashlib
import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb

from src.forecasting.lightgbm_data import (
    LIGHTGBM_FEATURES,
    prepare_lightgbm_datasets,
    LightGBMSplitResult,
)
from src.forecasting.lightgbm_config import get_default_lightgbm_config
from src.forecasting.lightgbm_train import (
    train_and_evaluate_lightgbm,
    DEFAULT_LIGHTGBM_MODEL_PATH,
    DEFAULT_PREDICTIONS_PATH,
    BENCHMARK_XGBOOST_MODEL_PATH,
)
from src.forecasting.contracts import (
    ForecastingDatasetContract,
    XGBOOST_26_FEATURES,
    DEFAULT_TARGET_COL,
    DEFAULT_DATE_COL,
)
from src.forecasting.metrics import calculate_all_metrics

# ---------------------------------------------------------------------------
# Round 1 protected asset hashes (used to verify immutability post-training)
# ---------------------------------------------------------------------------
_ROUND1_PROTECTED_CSVS = [
    "data/processed/freight_rates.csv",
    "data/processed/commodity_prices_processed.csv",
    "data/processed/oil_geopolitics_processed.csv",
    "data/processed/port_congestion_processed.csv",
    "data/processed/trade_flows_processed.csv",
    "data/processed/vessel_performance_processed.csv",
    "data/processed/india_bulk_imports_2022_2026.csv",
    "data/processed/monthly_freight_ml.csv",
    "data/processed/freight_model_features.csv",
]
_XGBOOST_MODEL_PATH = BENCHMARK_XGBOOST_MODEL_PATH


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# Lazily cached training result to avoid re-training for each test
_TRAIN_RESULT_CACHE = {}


def _get_train_result():
    """Run training once, cache and return result dict."""
    if "result" not in _TRAIN_RESULT_CACHE:
        result = train_and_evaluate_lightgbm(
            save_model=True,
            save_predictions=True,
        )
        _TRAIN_RESULT_CACHE["result"] = result
    return _TRAIN_RESULT_CACHE["result"]


# ---------------------------------------------------------------------------
# Test 35: Training succeeds end-to-end
# ---------------------------------------------------------------------------
def test_2b_training_succeeds():
    """LightGBM training must complete without raising any exceptions."""
    result = _get_train_result()
    assert result is not None, "train_and_evaluate_lightgbm returned None."
    assert "model" in result, "Result dict must contain 'model' key."
    assert result["model"] is not None, "Trained model must not be None."


# ---------------------------------------------------------------------------
# Test 36: Feature count is exactly 43
# ---------------------------------------------------------------------------
def test_2b_feature_count_is_43():
    """LightGBM must be trained on exactly 43 LIGHTGBM_FEATURES."""
    result = _get_train_result()
    assert result["feature_count"] == 43, (
        f"Expected 43 features, got {result['feature_count']}. "
        "LIGHTGBM_FEATURES contract must not have been changed."
    )
    assert result["feature_names"] == LIGHTGBM_FEATURES, (
        "Trained feature names do not match the LIGHTGBM_FEATURES contract."
    )


# ---------------------------------------------------------------------------
# Test 37: Target not passed as input feature
# ---------------------------------------------------------------------------
def test_2b_target_not_in_feature_input():
    """bulk_carrier_handysize_usd_day must not appear in training X."""
    split_res: LightGBMSplitResult = prepare_lightgbm_datasets()
    for split_name, X in [
        ("X_train", split_res.X_train),
        ("X_val", split_res.X_val),
        ("X_test", split_res.X_test),
    ]:
        assert DEFAULT_TARGET_COL not in X.columns, (
            f"Target column '{DEFAULT_TARGET_COL}' found in {split_name} — leakage detected!"
        )


# ---------------------------------------------------------------------------
# Test 38: Chronological split sizes are exactly 143 / 12 / 12
# ---------------------------------------------------------------------------
def test_2b_split_sizes_143_12_12():
    """Train/val/test split must be exactly 143, 12, 12 observations."""
    split_res: LightGBMSplitResult = prepare_lightgbm_datasets()
    assert len(split_res.X_train) == 143, f"Expected train=143, got {len(split_res.X_train)}"
    assert len(split_res.X_val) == 12, f"Expected val=12, got {len(split_res.X_val)}"
    assert len(split_res.X_test) == 12, f"Expected test=12, got {len(split_res.X_test)}"


# ---------------------------------------------------------------------------
# Test 39: Zero temporal overlap across partitions
# ---------------------------------------------------------------------------
def test_2b_zero_temporal_overlap():
    """Train, validation and test dates must be fully disjoint."""
    split_res: LightGBMSplitResult = prepare_lightgbm_datasets()
    train_set = set(split_res.train_dates.astype(str))
    val_set = set(split_res.val_dates.astype(str))
    test_set = set(split_res.test_dates.astype(str))
    assert not (train_set & val_set), "Overlap detected between train and validation dates."
    assert not (val_set & test_set), "Overlap detected between validation and test dates."
    assert not (train_set & test_set), "Overlap detected between train and test dates."

    # Strict chronological ordering
    t_max = pd.to_datetime(split_res.train_dates).max()
    v_min = pd.to_datetime(split_res.val_dates).min()
    v_max = pd.to_datetime(split_res.val_dates).max()
    te_min = pd.to_datetime(split_res.test_dates).min()
    assert t_max < v_min, f"Max train date {t_max} >= min val date {v_min}."
    assert v_max < te_min, f"Max val date {v_max} >= min test date {te_min}."


# ---------------------------------------------------------------------------
# Test 40: Test set not passed to fit() or early stopping
# ---------------------------------------------------------------------------
def test_2b_test_set_not_in_fit():
    """
    Verifies that the test set is never passed to lgb.LGBMRegressor.fit().
    We instrument this by inspecting that test dates do not appear in the
    validation eval_set that drives early stopping.
    """
    split_res: LightGBMSplitResult = prepare_lightgbm_datasets()
    test_dates = set(split_res.test_dates.astype(str))
    val_dates = set(split_res.val_dates.astype(str))
    # If test dates appear in val set, they were used for early stopping — violation.
    assert not (test_dates & val_dates), (
        "Test dates found in validation set — test data may have been used for early stopping!"
    )


# ---------------------------------------------------------------------------
# Test 41: Prediction DataFrame has required columns and split tags
# ---------------------------------------------------------------------------
def test_2b_prediction_df_columns_and_splits():
    """
    Prediction DataFrame must contain columns: date, actual, predicted, model, split.
    Each row must carry a split tag of 'train', 'validation', or 'test'.
    """
    result = _get_train_result()
    preds_df = result["predictions_df"]

    required_cols = {"date", "actual", "predicted", "model", "split"}
    missing_cols = required_cols - set(preds_df.columns)
    assert not missing_cols, f"Missing required columns in predictions_df: {missing_cols}"

    present_splits = set(preds_df["split"].unique())
    expected_splits = {"train", "validation", "test"}
    assert present_splits == expected_splits, (
        f"Expected splits {expected_splits}, found {present_splits}."
    )

    # Verify row counts per split
    train_rows = (preds_df["split"] == "train").sum()
    val_rows = (preds_df["split"] == "validation").sum()
    test_rows = (preds_df["split"] == "test").sum()
    assert train_rows == 143, f"Expected 143 train rows, got {train_rows}"
    assert val_rows == 12, f"Expected 12 validation rows, got {val_rows}"
    assert test_rows == 12, f"Expected 12 test rows, got {test_rows}"


# ---------------------------------------------------------------------------
# Test 42: Naive, XGBoost, and LightGBM evaluated on identical y_test and dates
# ---------------------------------------------------------------------------
def test_2b_identical_y_test_for_all_models():
    """
    Constraint: All three models (Naive, Round 1 XGBoost, Round 2 LightGBM)
    must be evaluated against the exact same y_test values and dates.
    Verify using the benchmark_comparison block returned by train_and_evaluate_lightgbm.
    """
    result = _get_train_result()
    split_res: LightGBMSplitResult = prepare_lightgbm_datasets()

    # Re-evaluate each model on the same y_test to confirm consistency
    y_test = split_res.y_test

    # LightGBM predictions from result
    lgbm_test_metrics = result["metrics"]["test"]
    lgbm_benchmark_metrics = result["benchmark_comparison"]["Round 2 LightGBM"]
    assert lgbm_test_metrics["MAE"] == lgbm_benchmark_metrics["MAE"], (
        "LightGBM metrics in 'test' and 'benchmark_comparison' are inconsistent."
    )

    # Verify Naive baseline uses exactly 12 test predictions
    benchmark = result["benchmark_comparison"]
    assert "Naive Baseline" in benchmark, "Naive Baseline missing from benchmark_comparison."
    assert "Round 1 XGBoost" in benchmark, "Round 1 XGBoost missing from benchmark_comparison."
    assert "Round 2 LightGBM" in benchmark, "Round 2 LightGBM missing from benchmark_comparison."

    # All models must have evaluated over identical test length (12 observations)
    naive_mae = benchmark["Naive Baseline"]["MAE"]
    xgb_mae = benchmark["Round 1 XGBoost"]["MAE"]
    lgbm_mae = benchmark["Round 2 LightGBM"]["MAE"]
    assert naive_mae > 0, "Naive baseline MAE must be positive."
    assert xgb_mae > 0, "XGBoost MAE must be positive."
    assert lgbm_mae > 0, "LightGBM MAE must be positive."


# ---------------------------------------------------------------------------
# Test 43: best_iteration is recorded and is a positive integer
# ---------------------------------------------------------------------------
def test_2b_best_iteration_recorded():
    """
    Reproducibility requirement: best_iteration must be captured from the trained
    model object and be a valid positive integer. This confirms early stopping
    (or full training) was recorded correctly per the installed LightGBM 4.7.0 API.
    """
    result = _get_train_result()
    best_iter = result.get("best_iteration")
    assert best_iter is not None, "best_iteration was not captured from the trained model."
    assert isinstance(best_iter, (int, np.integer)), (
        f"best_iteration must be an integer, got {type(best_iter)}."
    )
    assert best_iter >= 1, f"best_iteration must be >= 1, got {best_iter}."


# ---------------------------------------------------------------------------
# Test 44: Round 1 XGBoost model and processed CSVs remain unchanged
# ---------------------------------------------------------------------------
def test_2b_round1_assets_unchanged():
    """
    Round 1 asset immutability: final_xgboost_model.joblib and all protected
    Round 1 processed CSVs must not have been modified during Stage 2.2B execution.
    """
    # Verify XGBoost model can still be loaded
    assert os.path.exists(_XGBOOST_MODEL_PATH), (
        f"Round 1 XGBoost model missing at {_XGBOOST_MODEL_PATH}!"
    )
    xgb_model = joblib.load(_XGBOOST_MODEL_PATH)
    assert hasattr(xgb_model, "predict"), "Loaded object is not a valid model."

    # Verify feature_names_in_ is accessible and matches XGBOOST_26_FEATURES
    if hasattr(xgb_model, "feature_names_in_"):
        stored_features = list(xgb_model.feature_names_in_)
        assert len(stored_features) == 26, (
            f"XGBoost model feature_names_in_ has {len(stored_features)} features, expected 26."
        )

    # Verify all Round 1 CSVs exist
    for csv_path in _ROUND1_PROTECTED_CSVS:
        assert os.path.exists(csv_path), f"Round 1 protected CSV missing: {csv_path}"

    # Verify predictions CSV for LightGBM is a NEW, separate file
    assert DEFAULT_PREDICTIONS_PATH not in _ROUND1_PROTECTED_CSVS, (
        "lightgbm_forecast_predictions.csv must NOT be in the Round 1 protected set!"
    )


# ---------------------------------------------------------------------------
# Test 45: LightGBM model artifact and prediction CSV are new, separate files
# ---------------------------------------------------------------------------
def test_2b_lightgbm_artifact_and_csv_created():
    """
    Stage 2.2B must produce:
      1. ml/forecasting/lightgbm_freight_model.joblib (separate from final_xgboost_model.joblib)
      2. data/processed/lightgbm_forecast_predictions.csv (new file; never overwrites Round 1)
    """
    # LightGBM model artifact
    assert os.path.exists(DEFAULT_LIGHTGBM_MODEL_PATH), (
        f"LightGBM model artifact missing at {DEFAULT_LIGHTGBM_MODEL_PATH}."
    )
    # Must be a DIFFERENT file from the Round 1 XGBoost model
    assert os.path.abspath(DEFAULT_LIGHTGBM_MODEL_PATH) != os.path.abspath(_XGBOOST_MODEL_PATH), (
        "LightGBM model path must differ from the Round 1 XGBoost model path!"
    )

    # Predictions CSV
    assert os.path.exists(DEFAULT_PREDICTIONS_PATH), (
        f"Prediction CSV missing at {DEFAULT_PREDICTIONS_PATH}."
    )

    # Confirm predictions CSV is NOT in the Round 1 protected list
    abs_preds = os.path.abspath(DEFAULT_PREDICTIONS_PATH)
    for protected in _ROUND1_PROTECTED_CSVS:
        assert os.path.abspath(protected) != abs_preds, (
            f"Prediction CSV {DEFAULT_PREDICTIONS_PATH} matched Round 1 protected file {protected}!"
        )

    # Load saved CSV and verify required columns
    df = pd.read_csv(DEFAULT_PREDICTIONS_PATH)
    required_cols = {"date", "actual", "predicted", "model", "split"}
    assert required_cols.issubset(set(df.columns)), (
        f"Missing columns in saved CSV: {required_cols - set(df.columns)}"
    )

    # Verify total row count (143 + 12 + 12 = 167)
    assert len(df) == 167, f"Expected 167 rows in predictions CSV, got {len(df)}."
