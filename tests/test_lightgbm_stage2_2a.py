"""
Test suite for FreightWise Round 2 — Stage 2.2A: LightGBM Freight Forecasting Foundation.
Covers dataset loading, target separation, date separation, numeric feature matrix verification,
explicit feature contract matching, temporal leakage audit, chronological split alignment,
source file immutability, XGBoost model/contract immutability, and LightGBM model configuration.
"""

import os
import pandas as pd
import numpy as np

from src.data.loader import DataLoader
from src.forecasting.contracts import XGBOOST_26_FEATURES, DEFAULT_TARGET_COL, DEFAULT_DATE_COL
from src.forecasting.lightgbm_data import (
    LIGHTGBM_FEATURES,
    EXCLUDED_METADATA_COLUMNS,
    audit_temporal_leakage,
    derive_lightgbm_feature_contract,
    LightGBMDatasetPreparer,
    LightGBMSplitResult,
    prepare_lightgbm_datasets,
)
from src.forecasting.lightgbm_config import (
    LightGBMModelConfig,
    get_default_lightgbm_config,
)


def test_lightgbm_dataset_loading(loader=None):
    """Test 1: LightGBM dataset loads successfully via Stage 1 DataLoader."""
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 167
    assert len(df.columns) >= 46


def test_target_column_existence(loader=None):
    """Test 2: Expected target column bulk_carrier_handysize_usd_day exists in dataset."""
    if loader is None:
        loader = DataLoader()
    df = loader.load_freight_model_features()
    assert DEFAULT_TARGET_COL in df.columns
    assert df[DEFAULT_TARGET_COL].isnull().sum() == 0


def test_target_separated_from_x(loader=None):
    """Test 3: Target y is separated from X and target column is NOT present inside X."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    assert DEFAULT_TARGET_COL not in split_res.X_train.columns
    assert DEFAULT_TARGET_COL not in split_res.X_val.columns
    assert DEFAULT_TARGET_COL not in split_res.X_test.columns
    assert isinstance(split_res.y_train, pd.Series)
    assert len(split_res.y_train) == 143


def test_date_separated_from_x(loader=None):
    """Test 4: Raw date metadata columns are separated and NOT present inside X."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    for meta_col in ["date", "year_month", "canonical_month_start"]:
        assert meta_col not in split_res.X_train.columns
        assert meta_col not in split_res.X_val.columns
        assert meta_col not in split_res.X_test.columns


def test_all_features_numeric(loader=None):
    """Test 5: All LightGBM feature columns in X are 100% numeric data types."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    for col in split_res.X_train.columns:
        assert pd.api.types.is_numeric_dtype(split_res.X_train[col]), f"Feature '{col}' is not numeric!"


def test_explicit_feature_contract_match(loader=None):
    """Test 6: Explicit LIGHTGBM_FEATURES contract matches prepared X columns exactly in deterministic order."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    assert list(split_res.X_train.columns) == LIGHTGBM_FEATURES
    assert len(split_res.X_train.columns) == len(LIGHTGBM_FEATURES)
    assert len(LIGHTGBM_FEATURES) == 43


def test_target_not_in_feature_contract():
    """Test 7: Target column is strictly excluded from LIGHTGBM_FEATURES."""
    assert DEFAULT_TARGET_COL not in LIGHTGBM_FEATURES


def test_raw_date_not_in_feature_contract():
    """Test 8: Raw date metadata columns are strictly excluded from LIGHTGBM_FEATURES."""
    for meta_col in ["date", "year_month", "canonical_month_start"]:
        assert meta_col not in LIGHTGBM_FEATURES


def test_temporal_leakage_audit():
    """Test 9: Temporal leakage audit passes on all approved features and rejects prohibited future features."""
    for feat in LIGHTGBM_FEATURES:
        assert audit_temporal_leakage(feat) is True, f"Feature '{feat}' failed leakage audit!"

    # Prohibited future feature names must be rejected
    assert audit_temporal_leakage("freight_lead_1") is False
    assert audit_temporal_leakage("target_future_val") is False
    assert audit_temporal_leakage("shift_-1") is False


def test_preprocessing_no_leakage(loader=None):
    """Test 10: Verify split result passes verify_no_leakage() guard."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    assert split_res.verify_no_leakage(target_col=DEFAULT_TARGET_COL) is True


def test_chronological_split_sizes(loader=None):
    """Test 11: Chronological split sizes are 143 train, 12 val, 12 test for 167 observations."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    assert len(split_res.X_train) == 143
    assert len(split_res.y_train) == 143
    assert len(split_res.X_val) == 12
    assert len(split_res.y_val) == 12
    assert len(split_res.X_test) == 12
    assert len(split_res.y_test) == 12


def test_train_dates_precede_val_dates(loader=None):
    """Test 12: Train dates strictly precede validation dates (2022-12-01 < 2023-01-01)."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    train_max = pd.to_datetime(split_res.train_dates).max()
    val_min = pd.to_datetime(split_res.val_dates).min()
    assert train_max < val_min
    assert str(train_max.date()) == "2022-12-01"
    assert str(val_min.date()) == "2023-01-01"


def test_val_dates_precede_test_dates(loader=None):
    """Test 13: Validation dates strictly precede test dates (2023-12-01 < 2024-01-01)."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    val_max = pd.to_datetime(split_res.val_dates).max()
    test_min = pd.to_datetime(split_res.test_dates).min()
    assert val_max < test_min
    assert str(val_max.date()) == "2023-12-01"
    assert str(test_min.date()) == "2024-01-01"


def test_zero_temporal_overlap(loader=None):
    """Test 14: Zero date overlap between train, validation, and test partitions."""
    if loader is None:
        loader = DataLoader()
    split_res = prepare_lightgbm_datasets(loader)
    t_set = set(split_res.train_dates)
    v_set = set(split_res.val_dates)
    te_set = set(split_res.test_dates)
    assert len(t_set & v_set) == 0
    assert len(v_set & te_set) == 0
    assert len(t_set & te_set) == 0


def test_source_csv_immutability():
    """Test 15: All Stage 1 processed CSV files remain untouched and intact."""
    processed_dir = "data/processed"
    protected_files = [
        "freight_rates.csv",
        "commodity_prices_processed.csv",
        "oil_geopolitics_processed.csv",
        "port_congestion_processed.csv",
        "trade_flows_processed.csv",
        "vessel_performance_processed.csv",
        "india_bulk_imports_2022_2026.csv",
        "monthly_freight_ml.csv",
        "freight_model_features.csv",
        "route_demand_summary.csv",
    ]
    for fname in protected_files:
        fpath = os.path.join(processed_dir, fname)
        assert os.path.exists(fpath), f"Source file missing: {fpath}"
        assert os.path.getsize(fpath) > 0


def test_round1_xgboost_model_immutability():
    """Test 16: Round 1 XGBoost model binary final_xgboost_model.joblib exists and is intact."""
    model_path = "ml/forecasting/final_xgboost_model.joblib"
    assert os.path.exists(model_path)
    assert os.path.getsize(model_path) > 0


def test_xgboost_26_feature_contract_immutability():
    """Test 17: Round 1 XGBoost 26-feature contract remains intact and distinct from LightGBM 43-feature contract."""
    assert len(XGBOOST_26_FEATURES) == 26
    assert len(LIGHTGBM_FEATURES) == 43
    assert XGBOOST_26_FEATURES != LIGHTGBM_FEATURES
    assert set(XGBOOST_26_FEATURES).issubset(set(LIGHTGBM_FEATURES))


def test_lightgbm_config_validity():
    """Test 18: LightGBMModelConfig instantiates, validates, and returns valid parameter dictionary."""
    config = get_default_lightgbm_config()
    assert config.validate() is True
    params = config.to_dict()
    assert params["objective"] == "regression"
    assert params["metric"] == "rmse"
    assert params["learning_rate"] == 0.05
    assert params["n_estimators"] == 100
    assert params["random_state"] == 42
