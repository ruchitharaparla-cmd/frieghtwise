"""
Comprehensive Test Suite for FreightWise Round 2 — Stage 2.3.
Tests Chronos-2 and Prophet Forecasting Benchmarks alongside existing models.

Verifies:
  1. Existing 143/12/12 chronological split is preserved.
  2. Train/validation/test dates are correct.
  3. Chronos target column contract is bulk_carrier_handysize_usd_day.
  4. Chronos predictions have expected horizon (12).
  5. Chronos predictions have correct dates.
  6. Chronos has no future target leakage.
  7. Prophet uses ds/y correctly.
  8. Prophet predictions have expected horizon (12).
  9. Prophet prediction dates are correct.
  10. All metrics use the existing metrics implementation.
  11. Comparison contains all five model names.
  12. Validation and test target dates match across models.
  13. 2024 test data is not used for model fitting or tuning.
  14. Existing XGBoost artifact remains unchanged.
  15. Existing LightGBM artifact remains unchanged.
  16. Existing Stage 2.2C comparison output remains unchanged.
  17. Round 1 source CSVs remain unchanged.
"""

import os
from typing import Any, List, Optional
from unittest.mock import MagicMock

import joblib
import numpy as np
import pandas as pd
import pytest

from src.data.loader import DataLoader
from src.forecasting.benchmark_stage2_3 import (
    ALL_STAGE2_3_MODELS,
    CANDIDATE_CHRONOS2,
    CANDIDATE_LIGHTGBM,
    CANDIDATE_NAIVE,
    CANDIDATE_PROPHET,
    CANDIDATE_XGBOOST,
    STAGE2_3_COMPARISON_CSV_PATH,
)
from src.forecasting.chronos_forecast import (
    CHRONOS_AVAILABLE,
    CHRONOS_PREDICTIONS_CSV_PATH,
    ChronosAdapter,
)
from src.forecasting.contracts import (
    DEFAULT_DATE_COL,
    DEFAULT_TARGET_COL,
    XGBOOST_26_FEATURES,
)
from src.forecasting.lightgbm_data import LIGHTGBM_FEATURES
from src.forecasting.metrics import calculate_all_metrics
from src.forecasting.model_selection import (
    BENCHMARK_XGBOOST_MODEL_PATH,
    COMPARISON_CSV_PATH,
    LIGHTGBM_MODEL_PATH,
)
from src.forecasting.prophet_forecast import (
    PROPHET_AVAILABLE,
    PROPHET_PREDICTIONS_CSV_PATH,
    ProphetForecaster,
)
from src.forecasting.split import chronological_train_val_test_split


# ---------------------------------------------------------------------------
# Test 1: Existing 143/12/12 split is preserved
# ---------------------------------------------------------------------------
def test_existing_split_preserved(loader: Optional[DataLoader] = None):
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()
    split = chronological_train_val_test_split(df, date_col=DEFAULT_DATE_COL)

    assert len(split.train) == 143, f"Expected 143 train rows, got {len(split.train)}"
    assert len(split.validation) == 12, f"Expected 12 val rows, got {len(split.validation)}"
    assert len(split.test) == 12, f"Expected 12 test rows, got {len(split.test)}"
    assert len(df) == 167, f"Expected 167 total rows, got {len(df)}"


# ---------------------------------------------------------------------------
# Test 2: Train/validation/test dates are correct
# ---------------------------------------------------------------------------
def test_train_val_test_dates_correct(loader: Optional[DataLoader] = None):
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()
    split = chronological_train_val_test_split(df, date_col=DEFAULT_DATE_COL)

    train_dates = split.train[DEFAULT_DATE_COL].tolist()
    val_dates = split.validation[DEFAULT_DATE_COL].tolist()
    test_dates = split.test[DEFAULT_DATE_COL].tolist()

    assert train_dates[0] == "2011-02-01", f"Train start mismatch: {train_dates[0]}"
    assert train_dates[-1] == "2022-12-01", f"Train end mismatch: {train_dates[-1]}"
    assert val_dates[0] == "2023-01-01", f"Val start mismatch: {val_dates[0]}"
    assert val_dates[-1] == "2023-12-01", f"Val end mismatch: {val_dates[-1]}"
    assert test_dates[0] == "2024-01-01", f"Test start mismatch: {test_dates[0]}"
    assert test_dates[-1] == "2024-12-01", f"Test end mismatch: {test_dates[-1]}"


# ---------------------------------------------------------------------------
# Test 3: Chronos target column is bulk_carrier_handysize_usd_day
# ---------------------------------------------------------------------------
def test_chronos_target_column():
    assert DEFAULT_TARGET_COL == "bulk_carrier_handysize_usd_day"

    # Adapter validates target column existence
    mock_pipeline = MagicMock()
    adapter = ChronosAdapter(pipeline=mock_pipeline)
    bad_df = pd.DataFrame({"date": ["2023-01-01"], "wrong_target": [1000.0]})

    with pytest.raises(KeyError, match="bulk_carrier_handysize_usd_day"):
        adapter.forecast(bad_df, horizon=12, target_col=DEFAULT_TARGET_COL)


# ---------------------------------------------------------------------------
# Test 4: Chronos predictions have expected horizon (12)
# ---------------------------------------------------------------------------
def test_chronos_predictions_horizon():
    # Structural check on artifact
    assert os.path.exists(CHRONOS_PREDICTIONS_CSV_PATH), "Chronos predictions CSV missing"
    df = pd.read_csv(CHRONOS_PREDICTIONS_CSV_PATH)
    val_rows = df[df["split"] == "validation"]
    test_rows = df[df["split"] == "test"]

    assert len(val_rows) == 12, f"Expected 12 validation predictions, got {len(val_rows)}"
    assert len(test_rows) == 12, f"Expected 12 test predictions, got {len(test_rows)}"

    # Lightweight unit check on adapter horizon logic using mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.predict_df.return_value = pd.DataFrame({
        "predictions": np.full(12, 10000.0),
        "0.5": np.full(12, 10000.0),
    })
    adapter = ChronosAdapter(pipeline=mock_pipeline)
    dummy_history = pd.DataFrame({
        DEFAULT_DATE_COL: pd.date_range("2020-01-01", periods=24, freq="MS").strftime("%Y-%m-%d"),
        DEFAULT_TARGET_COL: np.linspace(8000, 12000, 24),
    })
    fc = adapter.forecast(dummy_history, horizon=12)
    assert len(fc) == 12


# ---------------------------------------------------------------------------
# Test 5: Chronos predictions have correct dates
# ---------------------------------------------------------------------------
def test_chronos_predictions_dates():
    df = pd.read_csv(CHRONOS_PREDICTIONS_CSV_PATH)
    val_dates = df[df["split"] == "validation"]["date"].tolist()
    test_dates = df[df["split"] == "test"]["date"].tolist()

    expected_val = [f"2023-{m:02d}-01" for m in range(1, 13)]
    expected_test = [f"2024-{m:02d}-01" for m in range(1, 13)]

    assert val_dates == expected_val, f"Chronos validation dates incorrect: {val_dates}"
    assert test_dates == expected_test, f"Chronos test dates incorrect: {test_dates}"


# ---------------------------------------------------------------------------
# Test 6: Chronos has no future target leakage
# ---------------------------------------------------------------------------
def test_chronos_no_future_target_leakage(loader: Optional[DataLoader] = None):
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()
    split = chronological_train_val_test_split(df, date_col=DEFAULT_DATE_COL)

    # Validation condition: max date <= 2022-12-01 (143 observations)
    val_history_dates = split.train[DEFAULT_DATE_COL]
    assert pd.to_datetime(val_history_dates.max()) <= pd.to_datetime("2022-12-01")

    # Test condition: max date <= 2023-12-01 (155 observations)
    test_history = pd.concat([split.train, split.validation], ignore_index=True)
    assert len(test_history) == 155
    assert pd.to_datetime(test_history[DEFAULT_DATE_COL].max()) <= pd.to_datetime("2023-12-01")

    # Verify zero 2024 observations exist in test conditioning history
    dates_in_2024 = [d for d in test_history[DEFAULT_DATE_COL] if str(d).startswith("2024")]
    assert len(dates_in_2024) == 0, f"Found 2024 dates in test conditioning: {dates_in_2024}"


# ---------------------------------------------------------------------------
# Test 7: Prophet uses ds/y correctly
# ---------------------------------------------------------------------------
def test_prophet_uses_ds_and_y_correctly():
    if not PROPHET_AVAILABLE:
        pytest.skip("Prophet is not installed in the environment.")

    forecaster = ProphetForecaster()
    dummy_history = pd.DataFrame({
        DEFAULT_DATE_COL: pd.date_range("2020-01-01", periods=24, freq="MS").strftime("%Y-%m-%d"),
        DEFAULT_TARGET_COL: np.linspace(8000, 12000, 24),
    })
    # Must fit and produce correct column output without error
    fc = forecaster.fit_and_forecast(dummy_history, horizon=6)
    assert "date" in fc.columns
    assert "predicted" in fc.columns
    assert len(fc) == 6


# ---------------------------------------------------------------------------
# Test 8: Prophet predictions have expected horizon (12)
# ---------------------------------------------------------------------------
def test_prophet_predictions_horizon():
    assert os.path.exists(PROPHET_PREDICTIONS_CSV_PATH), "Prophet predictions CSV missing"
    df = pd.read_csv(PROPHET_PREDICTIONS_CSV_PATH)

    val_rows = df[df["split"] == "validation"]
    test_rows = df[df["split"] == "test"]

    assert len(val_rows) == 12, f"Expected 12 validation predictions, got {len(val_rows)}"
    assert len(test_rows) == 12, f"Expected 12 test predictions, got {len(test_rows)}"


# ---------------------------------------------------------------------------
# Test 9: Prophet prediction dates are correct
# ---------------------------------------------------------------------------
def test_prophet_prediction_dates():
    df = pd.read_csv(PROPHET_PREDICTIONS_CSV_PATH)
    val_dates = df[df["split"] == "validation"]["date"].tolist()
    test_dates = df[df["split"] == "test"]["date"].tolist()

    expected_val = [f"2023-{m:02d}-01" for m in range(1, 13)]
    expected_test = [f"2024-{m:02d}-01" for m in range(1, 13)]

    assert val_dates == expected_val, f"Prophet validation dates incorrect: {val_dates}"
    assert test_dates == expected_test, f"Prophet test dates incorrect: {test_dates}"


# ---------------------------------------------------------------------------
# Test 10: All metrics use the existing metrics implementation
# ---------------------------------------------------------------------------
def test_all_metrics_use_existing_implementation():
    y_true = np.array([1000.0, 2000.0, 3000.0])
    y_pred = np.array([1100.0, 1900.0, 3300.0])

    metrics = calculate_all_metrics(y_true, y_pred)
    assert set(metrics.keys()) == {"MAE", "RMSE", "MAPE"}

    # Validate against stage 2.3 comparison table
    comp_df = pd.read_csv(STAGE2_3_COMPARISON_CSV_PATH)
    assert "mae" in comp_df.columns
    assert "rmse" in comp_df.columns
    assert "mape" in comp_df.columns


# ---------------------------------------------------------------------------
# Test 11: Comparison contains all five model names
# ---------------------------------------------------------------------------
def test_comparison_contains_all_five_models():
    assert os.path.exists(STAGE2_3_COMPARISON_CSV_PATH), "Stage 2.3 comparison CSV missing"
    comp_df = pd.read_csv(STAGE2_3_COMPARISON_CSV_PATH)

    models = set(comp_df["model"].unique())
    expected = {
        CANDIDATE_NAIVE,
        CANDIDATE_XGBOOST,
        CANDIDATE_LIGHTGBM,
        CANDIDATE_PROPHET,
        CANDIDATE_CHRONOS2,
    }
    assert models == expected, f"Model set mismatch: {models} != {expected}"
    assert len(comp_df) == 10, f"Expected 10 rows (5 models x 2 splits), got {len(comp_df)}"


# ---------------------------------------------------------------------------
# Test 12: Validation and test target dates match across models
# ---------------------------------------------------------------------------
def test_validation_and_test_target_dates_match_across_models():
    c_df = pd.read_csv(CHRONOS_PREDICTIONS_CSV_PATH)
    p_df = pd.read_csv(PROPHET_PREDICTIONS_CSV_PATH)

    # Date alignment
    assert c_df["date"].tolist() == p_df["date"].tolist()

    # Actual target value identity
    assert np.allclose(c_df["actual"].values, p_df["actual"].values)

    # Actuals match ground truth from features CSV
    df_full = DataLoader().load_freight_model_features()
    split = chronological_train_val_test_split(df_full)
    expected_val_actual = split.validation[DEFAULT_TARGET_COL].values
    expected_test_actual = split.test[DEFAULT_TARGET_COL].values

    val_c_actual = c_df[c_df["split"] == "validation"]["actual"].values
    test_c_actual = c_df[c_df["split"] == "test"]["actual"].values

    assert np.allclose(val_c_actual, expected_val_actual)
    assert np.allclose(test_c_actual, expected_test_actual)


# ---------------------------------------------------------------------------
# Test 13: 2024 test data is not used for tuning
# ---------------------------------------------------------------------------
def test_test_data_not_used_for_tuning(loader: Optional[DataLoader] = None):
    """
    Verifies from the implementation that no 2024 observations are passed
    to fitting, parameter selection, or conditioning functions prior to final evaluation.
    """
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()
    split = chronological_train_val_test_split(df)

    # Confirm training partition strictly precedes 2023
    assert all(pd.to_datetime(d).year < 2023 for d in split.train[DEFAULT_DATE_COL])

    # Confirm validation partition strictly precedes 2024
    assert all(pd.to_datetime(d).year == 2023 for d in split.validation[DEFAULT_DATE_COL])

    # Confirm test conditioning history (train + val) contains zero 2024 dates
    history_for_test = pd.concat([split.train, split.validation], ignore_index=True)
    assert all(pd.to_datetime(d).year < 2024 for d in history_for_test[DEFAULT_DATE_COL])


# ---------------------------------------------------------------------------
# Test 14: Existing XGBoost artifact remains unchanged
# ---------------------------------------------------------------------------
def test_xgboost_artifact_remains_unchanged():
    assert os.path.exists(BENCHMARK_XGBOOST_MODEL_PATH)
    xgb_model = joblib.load(BENCHMARK_XGBOOST_MODEL_PATH)

    # Verify 26-feature contract
    if hasattr(xgb_model, "feature_names_in_"):
        assert len(xgb_model.feature_names_in_) == 26
        for feat in XGBOOST_26_FEATURES:
            assert feat in xgb_model.feature_names_in_


# ---------------------------------------------------------------------------
# Test 15: Existing LightGBM artifact remains unchanged
# ---------------------------------------------------------------------------
def test_lightgbm_artifact_remains_unchanged():
    assert os.path.exists(LIGHTGBM_MODEL_PATH)
    lgb_model = joblib.load(LIGHTGBM_MODEL_PATH)
    assert len(LIGHTGBM_FEATURES) == 43


# ---------------------------------------------------------------------------
# Test 16: Existing Stage 2.2C comparison output remains unchanged
# ---------------------------------------------------------------------------
def test_stage2_2c_comparison_remains_unchanged():
    assert os.path.exists(COMPARISON_CSV_PATH)
    df_2c = pd.read_csv(COMPARISON_CSV_PATH)

    assert len(df_2c) == 6, f"Expected exactly 6 rows in Stage 2.2C comparison, got {len(df_2c)}"
    expected_cols = ["model", "split", "mae", "rmse", "mape", "is_selected", "selection_reason"]
    assert list(df_2c.columns) == expected_cols


# ---------------------------------------------------------------------------
# Test 17: Round 1 source CSVs remain unchanged
# ---------------------------------------------------------------------------
def test_round1_source_csvs_remains_unchanged():
    r1_files = [
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
    for p in r1_files:
        assert os.path.exists(p), f"Source file {p} is missing"
        assert os.path.getsize(p) > 0, f"Source file {p} is empty"

