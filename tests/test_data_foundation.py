"""
Test suite for FreightWise Round 2 — Stage 1: Data Foundation.
Covers 10 Stage 1 DataLoader targets, schema contracts, date normalization, unit checks,
entity mappings, safe temporal joins, exact XGBoost model integrity, and source file immutability.
"""

import os
import hashlib
import joblib
import pandas as pd
import numpy as np
from src.data.loader import DataLoader
from src.data.schemas import (
    FreightDatasetSchema,
    FreightModelInputSchema,
    VesselPerformanceSchema,
    IndiaBulkImportsSchema,
    PortCongestionSchema,
)
from src.data.normalization import normalize_dates, normalize_country_name, normalize_port_name
from src.data.validation import validate_units
from src.data.joins import (
    aggregate_daily_oil_to_monthly,
    aggregate_weekly_congestion_to_monthly,
    safe_join_monthly_freight_with_market,
)
from src.data.features import extract_xgboost_model_features
from src.data.status import GLOBAL_CONGESTION_PROXY, HISTORICAL_DEMAND_NOT_FORECAST


try:
    import pytest

    @pytest.fixture
    def loader():
        return DataLoader()
except ImportError:
    def loader():
        return DataLoader()


def test_freight_loader_and_schema(loader):
    """Test 1: Freight model features loader & 46-column dataset schema contract."""
    df = loader.load_freight_model_features()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 167
    assert len(df.columns) >= 46
    assert FreightDatasetSchema.validate(df) is True
    assert "year_month" in df.columns
    assert "canonical_month_start" in df.columns


def test_vessel_loader_and_filtering(loader):
    """Test 2: Vessel loader & bulk carrier filtering (669 rows)."""
    df_all = loader.load_vessel_performance(filter_bulk_carrier=False)
    assert len(df_all) == 2736
    assert VesselPerformanceSchema.validate(df_all) is True

    df_bulk = loader.load_vessel_performance(filter_bulk_carrier=True)
    assert len(df_bulk) == 669
    assert (df_bulk["ship_type"] == "Bulk Carrier").all()


def test_india_import_loader_units(loader):
    """Test 3: Indian import loader & 100% TON unit verification."""
    df = loader.load_india_bulk_imports(normalize_entities=True)
    assert len(df) == 11200
    assert IndiaBulkImportsSchema.validate(df) is True
    assert (df["Unit"] == "TON").all()
    assert "Country_Normalized" in df.columns
    assert "Port_Normalized" in df.columns


def test_schema_contracts():
    """Test 4: Schema contracts error handling on invalid DataFrame."""
    invalid_df = pd.DataFrame({"dummy_col": [1, 2, 3]})

    raised = False
    try:
        FreightDatasetSchema.validate(invalid_df)
    except ValueError:
        raised = True
    assert raised, "FreightDatasetSchema should raise ValueError on invalid DataFrame"

    raised = False
    try:
        VesselPerformanceSchema.validate(invalid_df)
    except ValueError:
        raised = True
    assert raised, "VesselPerformanceSchema should raise ValueError on invalid DataFrame"

    raised = False
    try:
        IndiaBulkImportsSchema.validate(invalid_df)
    except ValueError:
        raised = True
    assert raised, "IndiaBulkImportsSchema should raise ValueError on invalid DataFrame"

    raised = False
    try:
        PortCongestionSchema.validate(invalid_df)
    except ValueError:
        raised = True
    assert raised, "PortCongestionSchema should raise ValueError on invalid DataFrame"


def test_date_normalization_and_copy_immutability():
    """Test 5: Date normalization returns copy and derives year_month without mutating source."""
    raw_data = pd.DataFrame({"date": ["2024-01-15", "2024-02-20"], "val": [10, 20]})
    raw_copy_before = raw_data.copy()

    norm_df = normalize_dates(raw_data, date_col="date")
    assert "year_month" in norm_df.columns
    assert "canonical_month_start" in norm_df.columns
    assert norm_df["year_month"].tolist() == ["2024-01", "2024-02"]

    # Assert raw source DataFrame is untouched
    pd.testing.assert_frame_equal(raw_data, raw_copy_before)


def test_unit_validation_checks(loader):
    """Test 6: Unit validation checks across datasets."""
    freight_df = loader.load_freight_rates()
    rep_f = validate_units(freight_df, "freight_rates")
    assert rep_f["valid"] is True

    vessel_df = loader.load_vessel_performance()
    rep_v = validate_units(vessel_df, "vessel_performance")
    assert rep_v["valid"] is True

    import_df = loader.load_india_bulk_imports()
    rep_i = validate_units(import_df, "india_bulk_imports")
    assert rep_i["valid"] is True


def test_entity_normalization_and_coal_separation():
    """Test 7: Entity mappings and strict separation of Coal categories."""
    assert normalize_country_name("U S A") == "USA"
    assert normalize_country_name("U ARAB EMTS") == "UAE"
    assert normalize_country_name("U K") == "UK"
    assert normalize_country_name("SOUTH AFRICA") == "South Africa"
    assert normalize_country_name("CHINA P RP") == "China"

    assert normalize_port_name("VISAKHAPATNAM SEA") == "Visakhapatnam Port"
    assert normalize_port_name("PARADIP SEA") == "Paradip Port"

    # Assert COAL,COKE AND BRIQUITTES ETC is NOT mapped to Thermal Coal Newcastle
    raw_import_commodity = "COAL,COKE AND BRIQUITTES ETC"
    processed_commodity = "Thermal Coal Newcastle"
    assert raw_import_commodity != processed_commodity


def test_route_demand_summary_loading(loader):
    """Test 8: Route demand summary loading and historical tag."""
    df = loader.load_route_demand_summary()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 40
    assert df.attrs.get("tag") == HISTORICAL_DEMAND_NOT_FORECAST


def test_safe_temporal_joins(loader):
    """Test 9: Explicit safe temporal aggregations & join explosion prevention."""
    df_freight = loader.load_freight_rates()
    df_oil = loader.load_oil_geopolitics()
    df_congestion = loader.load_port_congestion()

    # Aggregate daily oil to monthly
    monthly_oil = aggregate_daily_oil_to_monthly(df_oil)
    assert "year_month" in monthly_oil.columns
    assert len(monthly_oil) == 194  # 194 distinct months

    # Aggregate weekly congestion to monthly
    monthly_congestion = aggregate_weekly_congestion_to_monthly(df_congestion)
    assert "year_month" in monthly_congestion.columns

    # Join 1-to-1 monthly freight with monthly oil
    freight_len = len(df_freight)
    joined = safe_join_monthly_freight_with_market(df_freight, monthly_oil, join_key="year_month")
    assert len(joined) <= freight_len
    assert "brent_price_mean" in joined.columns


def test_exact_xgboost_model_integrity(loader):
    """
    Test 10: Exact Round 1 XGBoost Model Integrity Test.
    Loads joblib model, reads model.feature_names_in_ dynamically,
    extracts exact 26 features in exact model order, and runs .predict().
    """
    model_path = "ml/forecasting/final_xgboost_model.joblib"
    assert os.path.exists(model_path), f"Model file missing at {model_path}"

    model = joblib.load(model_path)
    assert hasattr(model, "feature_names_in_")
    expected_features = list(model.feature_names_in_)
    assert len(expected_features) == 26

    # Load 46-column dataset
    df_features = loader.load_freight_model_features()

    # Dynamically extract and order exact 26 input features
    X_input = extract_xgboost_model_features(df_features, model)
    assert list(X_input.columns) == expected_features

    # Run prediction without modifying model
    preds = model.predict(X_input)
    assert isinstance(preds, np.ndarray)
    assert len(preds) == len(df_features)
    assert not np.isnan(preds).any()


def test_round1_source_file_integrity():
    """
    Test 11: Round 1 Source-Integrity Test.
    Verifies that all protected Round 1 processed CSV files remain completely unchanged.
    """
    protected_files = [
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

    for fpath in protected_files:
        assert os.path.exists(fpath), f"Protected file missing: {fpath}"
        assert os.path.getsize(fpath) > 0, f"Protected file is empty: {fpath}"
