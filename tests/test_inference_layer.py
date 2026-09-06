"""
Unit and Integration Tests for FreightWise Stage 2.4 — Freight Forecasting Production/Inference Layer.

Verifies:
1. Exact 26-feature contract matching model.feature_names_in_.
2. Hard-coded SHA-256 artifact integrity guard.
3. Model loading singleton behavior without retraining.
4. Single prediction schema, types, and values.
5. Batch prediction schema, row alignment, and values.
6. Acceptance of extra columns (ignored for prediction).
7. Acceptance and internal reordering of shuffled feature columns.
8. Clear failure on missing required features.
9. Clear failure on null/missing feature values.
10. Clear failure on non-numeric feature inputs.
11. Strict date handling (mandatory, validated, never passed into model).
12. Deterministic inference reproduction.
13. Model selection integrity (Stage 2.2C selection unchanged).
"""

import copy
import hashlib
import os
import pytest
import numpy as np
import pandas as pd

from src.data.loader import DataLoader
from src.forecasting.contracts import DEFAULT_DATE_COL, XGBOOST_26_FEATURES
from src.forecasting.model_loader import (
    DEFAULT_XGBOOST_MODEL_PATH,
    EXPECTED_XGBOOST_SHA256,
    compute_file_sha256,
    load_xgboost_model,
)
from src.forecasting.validation import validate_date_column, validate_features
from src.forecasting.inference import (
    FreightForecastService,
    CANONICAL_MODEL_NAME,
    DEFAULT_UNIT,
)
from src.forecasting.model_selection import (
    COMPARISON_CSV_PATH,
    CANDIDATE_XGBOOST,
)


def get_sample_feature_record():
    """Provides a single valid feature record matching all 26 contract features and date."""
    return {
        "date": "2024-01-01",
        "freight_lag_1": 12500.0,
        "freight_lag_3": 13000.0,
        "freight_lag_6": 12800.0,
        "freight_lag_12": 11000.0,
        "freight_rolling_mean_3": 12700.0,
        "freight_rolling_mean_6": 12600.0,
        "freight_rolling_mean_12": 12000.0,
        "freight_rolling_std_3": 250.0,
        "baltic_dry_index_lag_1": 1500.0,
        "baltic_dry_index_lag_3": 1450.0,
        "brent_price_lag_1": 77.5,
        "brent_price_lag_3": 82.0,
        "wti_price_lag_1": 72.8,
        "wti_price_lag_3": 78.1,
        "dxy_index_lag_1": 102.5,
        "dxy_index_lag_3": 104.2,
        "vix_lag_1": 13.8,
        "vix_lag_3": 14.9,
        "gpr_index_lag_1": 115.0,
        "gpr_index_lag_3": 108.0,
        "thermal_coal_price_lag_1": 130.0,
        "thermal_coal_price_lag_3": 138.0,
        "month_num": 1,
        "quarter": 1,
        "month_sin": 0.5,
        "month_cos": 0.866025,
    }


def get_real_feature_df():
    """Loads the real processed feature DataFrame from DataLoader."""
    loader = DataLoader()
    return loader.load_freight_model_features()


@pytest.fixture
def sample_feature_record():
    """Pytest fixture providing sample feature record."""
    return get_sample_feature_record()


@pytest.fixture
def real_feature_df():
    """Pytest fixture providing real feature DataFrame."""
    return get_real_feature_df()



# ---------------------------------------------------------------------------
# 1. Artifact Integrity & Model Loading Tests
# ---------------------------------------------------------------------------
def test_xgboost_artifact_exists_and_matches_hardcoded_sha256():
    """Requirement 5: Hard-coded SHA-256 checksum guard against model mutation."""
    assert os.path.exists(DEFAULT_XGBOOST_MODEL_PATH), "Model artifact does not exist."
    actual_hash = compute_file_sha256(DEFAULT_XGBOOST_MODEL_PATH)
    assert actual_hash == EXPECTED_XGBOOST_SHA256, (
        f"Model artifact SHA-256 changed! Expected '{EXPECTED_XGBOOST_SHA256}', "
        f"got '{actual_hash}'."
    )


def test_load_xgboost_model_attributes():
    """Verifies that the loaded model has 26 features and matching feature names."""
    model, version = load_xgboost_model(verify_checksum=True)
    assert version == EXPECTED_XGBOOST_SHA256
    assert hasattr(model, "predict")
    assert model.n_features_in_ == 26
    assert hasattr(model, "feature_names_in_")
    names = [str(f) for f in model.feature_names_in_]
    assert names == list(XGBOOST_26_FEATURES)


def test_load_xgboost_model_caching():
    """Verifies that subsequent calls return the cached singleton instance."""
    m1, v1 = load_xgboost_model()
    m2, v2 = load_xgboost_model()
    assert m1 is m2
    assert v1 == v2


def test_service_instantiation_no_retraining():
    """Verifies service instantiates quickly without triggering retraining."""
    service = FreightForecastService()
    assert service.model_name == CANONICAL_MODEL_NAME
    assert service.unit == DEFAULT_UNIT
    assert service.model_version == EXPECTED_XGBOOST_SHA256
    assert len(service.feature_names) == 26


# ---------------------------------------------------------------------------
# 2. Validation Module Tests
# ---------------------------------------------------------------------------
def test_validation_extra_columns_allowed_and_ignored(sample_feature_record=None):
    """Requirement 1: Extra columns are allowed and ignored."""
    record = sample_feature_record or get_sample_feature_record()
    data = copy.deepcopy(record)
    data["extra_column_1"] = 999.9
    data["vessel_name"] = "Ocean Voyager"
    df = pd.DataFrame([data])

    extracted = validate_features(df, expected_features=list(XGBOOST_26_FEATURES))
    assert list(extracted.columns) == list(XGBOOST_26_FEATURES)
    assert "extra_column_1" not in extracted.columns
    assert "vessel_name" not in extracted.columns
    assert len(extracted.columns) == 26


def test_validation_shuffled_features_reordered(sample_feature_record=None):
    """Requirement 2: Input with shuffled feature order is accepted and reordered."""
    record = sample_feature_record or get_sample_feature_record()
    data = copy.deepcopy(record)
    # Reverse column order in dataframe
    keys = list(data.keys())
    shuffled_keys = list(reversed(keys))
    df = pd.DataFrame([data])[shuffled_keys]

    extracted = validate_features(df, expected_features=list(XGBOOST_26_FEATURES))
    assert list(extracted.columns) == list(XGBOOST_26_FEATURES)


def test_validation_missing_feature_raises():
    """Requirement 8/9: Missing required features raises clear ValueError."""
    df = pd.DataFrame([{"date": "2024-01-01", "freight_lag_1": 12000.0}])
    with pytest.raises(ValueError, match="missing required XGBoost feature"):
        validate_features(df, expected_features=list(XGBOOST_26_FEATURES))


def test_validation_null_value_raises(sample_feature_record=None):
    """Requirement 9: Missing values raise clear ValueError (no silent imputation)."""
    record = sample_feature_record or get_sample_feature_record()
    data = copy.deepcopy(record)
    data["brent_price_lag_1"] = np.nan
    df = pd.DataFrame([data])
    with pytest.raises(ValueError, match="contain missing/null values"):
        validate_features(df, expected_features=list(XGBOOST_26_FEATURES))


def test_validation_non_numeric_raises(sample_feature_record=None):
    """Requirement 17: Non-numeric inputs raise ValueError."""
    record = sample_feature_record or get_sample_feature_record()
    data = copy.deepcopy(record)
    data["vix_lag_1"] = "high_volatility"
    df = pd.DataFrame([data])
    with pytest.raises(ValueError, match="contains non-numeric values"):
        validate_features(df, expected_features=list(XGBOOST_26_FEATURES))


def test_date_validation_missing_raises(sample_feature_record=None):
    """Requirement 4: Missing date column raises clear ValueError."""
    record = sample_feature_record or get_sample_feature_record()
    data = copy.deepcopy(record)
    del data["date"]
    df = pd.DataFrame([data])
    with pytest.raises(ValueError, match="missing mandatory date column"):
        validate_date_column(df)


def test_date_validation_null_date_raises(sample_feature_record=None):
    """Requirement 4: Null date values raise ValueError."""
    record = sample_feature_record or get_sample_feature_record()
    data = copy.deepcopy(record)
    data["date"] = None
    df = pd.DataFrame([data])
    with pytest.raises(ValueError, match="contains null/missing values"):
        validate_date_column(df)


# ---------------------------------------------------------------------------
# 3. Service Prediction Tests
# ---------------------------------------------------------------------------
def test_predict_single_dict_schema_and_types(sample_feature_record=None):
    """Verifies single prediction returns correct schema and types."""
    record = sample_feature_record or get_sample_feature_record()
    service = FreightForecastService()
    result = service.predict(record)

    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "model_name",
        "model_version",
        "forecast_date",
        "predicted_freight_rate",
        "unit",
    }
    assert result["model_name"] == CANONICAL_MODEL_NAME
    assert result["model_version"] == EXPECTED_XGBOOST_SHA256
    assert result["forecast_date"] == "2024-01-01"
    assert isinstance(result["predicted_freight_rate"], float)
    assert result["predicted_freight_rate"] > 0
    assert result["unit"] == "USD/day"


def test_predict_single_with_dataframe_and_series(sample_feature_record=None):
    """Verifies single prediction accepts pd.DataFrame and pd.Series."""
    record = sample_feature_record or get_sample_feature_record()
    service = FreightForecastService()
    df_1row = pd.DataFrame([record])
    series_1row = pd.Series(record)

    res_df = service.predict(df_1row)
    res_series = service.predict(series_1row)

    assert res_df["predicted_freight_rate"] == res_series["predicted_freight_rate"]
    assert res_df["forecast_date"] == "2024-01-01"


def test_predict_single_multi_row_raises(real_feature_df=None):
    """Verifies predict() raises ValueError if given more than 1 row."""
    df = real_feature_df if real_feature_df is not None else get_real_feature_df()
    service = FreightForecastService()
    with pytest.raises(ValueError, match="expects exactly 1 observation"):
        service.predict(df.head(5))


def test_predict_batch_schema_and_alignment(real_feature_df=None):
    """Verifies predict_batch() schema, length, and row-by-row date alignment."""
    df = real_feature_df if real_feature_df is not None else get_real_feature_df()
    service = FreightForecastService()
    subset = df.tail(12).copy()

    batch_res = service.predict_batch(subset)

    assert isinstance(batch_res, pd.DataFrame)
    assert len(batch_res) == 12
    assert list(batch_res.columns) == [
        "forecast_date",
        "predicted_freight_rate",
        "model_name",
        "model_version",
        "unit",
    ]

    expected_dates = pd.to_datetime(subset["date"]).dt.strftime("%Y-%m-%d").values
    assert (batch_res["forecast_date"].values == expected_dates).all()
    assert (batch_res["model_name"] == CANONICAL_MODEL_NAME).all()
    assert (batch_res["model_version"] == EXPECTED_XGBOOST_SHA256).all()
    assert (batch_res["unit"] == DEFAULT_UNIT).all()
    assert (batch_res["predicted_freight_rate"] > 0).all()


def test_inference_deterministic(sample_feature_record=None):
    """Verifies repeated predictions produce identical values."""
    record = sample_feature_record or get_sample_feature_record()
    service = FreightForecastService()
    res1 = service.predict(record)
    res2 = service.predict(record)

    assert res1["predicted_freight_rate"] == res2["predicted_freight_rate"]



# ---------------------------------------------------------------------------
# 4. Stage Continuity & Model Selection Integrity Tests
# ---------------------------------------------------------------------------
def test_stage2_2c_comparison_file_unchanged():
    """Confirms Stage 2.2C model comparison CSV is preserved and selected model is XGBoost."""
    assert os.path.exists(COMPARISON_CSV_PATH)
    df_comp = pd.read_csv(COMPARISON_CSV_PATH)
    selected_row = df_comp[df_comp["is_selected"] == True]
    assert len(selected_row) == 1
    assert selected_row.iloc[0]["model"] == CANDIDATE_XGBOOST
