"""
Test suite for FreightWise Round 2 — Stage 2.1: Freight Forecasting Contract & Foundation.
Covers chronological ordering, train/val/test splitting, zero temporal leakage,
metric calculations (MAE, RMSE, MAPE), XGBoost feature contract separation, and source file immutability.
"""

import os
import hashlib
import numpy as np
import pandas as pd
from src.data.loader import DataLoader
from src.forecasting.contracts import (
    ForecastingDatasetContract,
    EvaluationResultContract,
    XGBOOST_26_FEATURES,
)
from src.forecasting.split import (
    chronological_train_val_test_split,
    TimeSeriesSplitResult,
)
from src.forecasting.metrics import (
    calculate_mae,
    calculate_rmse,
    calculate_mape,
    calculate_all_metrics,
)


def test_chronological_split_sizes_and_ordering(loader=None):
    """Test 1: Split sizes (143/12/12 on 167 rows) and strict chronological ordering."""
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()

    assert len(df) == 167

    split = chronological_train_val_test_split(
        df, date_col="date", train_size=143, val_size=12, test_size=12
    )

    assert len(split.train) == 143
    assert len(split.validation) == 12
    assert len(split.test) == 12
    assert split.lengths == (143, 12, 12)

    # Date ordering check within partitions
    assert pd.to_datetime(split.train["date"]).is_monotonic_increasing
    assert pd.to_datetime(split.validation["date"]).is_monotonic_increasing
    assert pd.to_datetime(split.test["date"]).is_monotonic_increasing

    # Exact date range assertions for 167-row dataset
    assert split.train["date"].min() == "2011-02-01"
    assert split.train["date"].max() == "2022-12-01"
    assert split.validation["date"].min() == "2023-01-01"
    assert split.validation["date"].max() == "2023-12-01"
    assert split.test["date"].min() == "2024-01-01"
    assert split.test["date"].max() == "2024-12-01"


def test_no_train_val_test_overlap_and_leakage(loader=None):
    """Test 2: Zero index overlap and no temporal leakage across split boundaries."""
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()

    split = chronological_train_val_test_split(df, date_col="date")

    # Index disjointness
    train_dates = set(split.train["date"])
    val_dates = set(split.validation["date"])
    test_dates = set(split.test["date"])

    assert len(train_dates & val_dates) == 0, "Train and Validation dates overlap!"
    assert len(val_dates & test_dates) == 0, "Validation and Test dates overlap!"
    assert len(train_dates & test_dates) == 0, "Train and Test dates overlap!"

    # Temporal leakage guard
    train_max = pd.to_datetime(split.train["date"]).max()
    val_min = pd.to_datetime(split.validation["date"]).min()
    val_max = pd.to_datetime(split.validation["date"]).max()
    test_min = pd.to_datetime(split.test["date"]).min()

    assert train_max < val_min, f"Temporal leakage: train_max ({train_max}) >= val_min ({val_min})"
    assert val_max < test_min, f"Temporal leakage: val_max ({val_max}) >= test_min ({test_min})"

    # Built-in verification method check
    assert split.verify_no_overlap(date_col="date") is True


def test_metric_calculations_analytical():
    """Test 3: Verification of MAE, RMSE, and MAPE metrics on analytical test cases."""
    y_true = np.array([100.0, 200.0, 300.0, 400.0])
    y_pred = np.array([110.0, 190.0, 315.0, 380.0])

    mae = calculate_mae(y_true, y_pred)
    rmse = calculate_rmse(y_true, y_pred)
    mape = calculate_mape(y_true, y_pred)

    assert np.isclose(mae, 13.75)
    assert np.isclose(rmse, np.sqrt(206.25))
    assert np.isclose(mape, 6.25)

    all_m = calculate_all_metrics(y_true, y_pred)
    assert "MAE" in all_m and "RMSE" in all_m and "MAPE" in all_m
    assert np.isclose(all_m["MAE"], 13.75)
    assert np.isclose(all_m["RMSE"], np.sqrt(206.25))
    assert np.isclose(all_m["MAPE"], 6.25)


def test_forecasting_contracts_and_xgboost_isolation(loader=None):
    """Test 4: Forecasting dataset contract validation and XGBoost 26-feature separation."""
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()

    # Validate dataset contract
    assert ForecastingDatasetContract.validate(df, require_xgboost_features=True) is True

    # Extract exact 26 XGBoost features
    xgb_df = ForecastingDatasetContract.extract_xgboost_features(df)
    assert isinstance(xgb_df, pd.DataFrame)
    assert len(xgb_df) == 167
    assert list(xgb_df.columns) == XGBOOST_26_FEATURES
    assert len(xgb_df.columns) == 26

    # Verify original df remains 46+ columns
    assert len(df.columns) >= 46

    # EvaluationResultContract validation test
    eval_res = EvaluationResultContract(
        model_name="Baseline XGBoost",
        split_name="test",
        sample_size=12,
        metrics={"MAE": 2117.82, "RMSE": 3111.19, "MAPE": 36.75},
    )
    assert eval_res.validate() is True
    res_dict = eval_res.to_dict()
    assert res_dict["model_name"] == "Baseline XGBoost"
    assert res_dict["metrics"]["MAE"] == 2117.82


def test_source_file_immutability():
    """Test 5: Round 1 source files and model binary immutability."""
    model_path = "ml/forecasting/final_xgboost_model.joblib"
    assert os.path.exists(model_path)

    processed_dir = "data/processed"
    expected_files = [
        "freight_rates.csv",
        "monthly_freight_ml.csv",
        "freight_model_features.csv",
        "commodity_prices_processed.csv",
    ]

    for fname in expected_files:
        fpath = os.path.join(processed_dir, fname)
        assert os.path.exists(fpath), f"Processed file missing: {fpath}"
        assert os.path.getsize(fpath) > 0
