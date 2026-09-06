"""
Unit and Integration Test Suite for FreightWise Stage 3 — Delay & Congestion Prediction.

Covers:
1. Reconciling 2,736 raw vessel rows -> 669 Bulk Carrier rows.
2. Vessel chronological split strictly satisfying max(train) < min(val) < min(test).
3. Exact 12 pre-voyage vessel features contract and zero leakage of turnaround target into classifier.
4. Port congestion panel lag calculation strictly per port entity (Addition 2: zero cross-port leakage).
5. Port congestion 1-week-ahead lead target definitions and zero future leakage.
6. India Port Absence Audit verifying 0 Indian ports in port congestion dataset.
7. Model evaluation comparison metrics including F1, Precision, Recall, ROC-AUC, PR-AUC (Addition 1).
8. Model training, joblib artifact creation, and artifact versioning.
9. VesselTurnaroundService and PortCongestionService inference schema and deterministic reproducibility.
10. IndiaPortDataAbsentError guard triggering on Indian port queries.
11. Immutability guards for Stage 1 source CSVs, Stage 2.2C XGBoost freight model, and Stage 2 CSVs.
"""

import os
import pytest
import numpy as np
import pandas as pd

from src.data.loader import DataLoader
from src.delays.contracts import (
    DELAY_RISK_THRESHOLD_HOURS,
    HIGH_CONGESTION_THRESHOLD_INDEX,
    PORT_CATEGORICAL_FEATURES,
    PORT_CONGESTION_FEATURES,
    VESSEL_CATEGORICAL_FEATURES,
    VESSEL_FEATURES_12,
    VESSEL_NUMERIC_FEATURES,
    PortCongestionContract,
    VesselDatasetContract,
)
from src.delays.vessel_turnaround import (
    VESSEL_COMPARISON_CSV_PATH,
    VESSEL_DELAY_RISK_MODEL_PATH,
    VESSEL_TURNAROUND_MODEL_PATH,
    train_and_evaluate_vessel_models,
)
from src.delays.port_congestion import (
    PORT_COMPARISON_CSV_PATH,
    PORT_CONGESTION_REGRESSOR_PATH,
    PORT_CONGESTION_CLASSIFIER_PATH,
    train_and_evaluate_port_congestion_models,
)
from src.delays.service import (
    IndiaPortDataAbsentError,
    PortCongestionService,
    VesselTurnaroundService,
)
from src.forecasting.model_loader import DEFAULT_XGBOOST_MODEL_PATH, EXPECTED_XGBOOST_SHA256, compute_file_sha256
from src.forecasting.model_selection import COMPARISON_CSV_PATH as STAGE2_2C_COMPARISON_CSV_PATH


def get_sample_vessel_input():
    return {
        "date": "2024-05-01",
        "route_type": "Australia-China",
        "engine_type": "MAN B&W 6S60ME",
        "maintenance_status": "Good",
        "weather_condition": "Moderate",
        "speed_over_ground_knots": 13.5,
        "engine_power_kw": 11000,
        "distance_traveled_nm": 3500,
        "draft_meters": 11.2,
        "cargo_weight_tons": 55000,
        "seasonal_impact_score": 1.1,
        "weekly_voyage_count": 12,
        "average_load_percentage": 88.5,
    }


def get_sample_port_input():
    return {
        "week_start": "2024-05-01",
        "port": "Shanghai",
        "country": "China",
        "region": "Asia",
        "month_num": 5,
        "year": 2024,
        "throughput_teu_mn": 45,
        "vessels_at_anchor": 22,
        "avg_wait_days": 2.1,
        "congestion_index": 1.8,
        "port_utilization_pct": 0.85,
        "berth_delay_hrs": 50.4,
        "vessels_at_anchor_lag1": 20,
        "avg_wait_days_lag1": 1.9,
        "congestion_index_lag1": 1.7,
        "berth_delay_hrs_lag1": 45.6,
        "vessels_at_anchor_lag2": 19,
        "avg_wait_days_lag2": 1.8,
        "congestion_index_lag2": 1.6,
    }


# ---------------------------------------------------------------------------
# 1. Vessel Data Contract & Leakage Tests
# ---------------------------------------------------------------------------
def test_vessel_filtering_pipeline_reconciles_669_rows():
    loader = DataLoader()
    raw_vessel = loader.load_vessel_performance()
    assert len(raw_vessel) == 2736, f"Expected 2,736 raw vessel rows, got {len(raw_vessel)}"

    bulk_df = VesselDatasetContract.validate_and_filter_bulk_carriers(raw_vessel)
    assert len(bulk_df) == 669, f"Expected exactly 669 Bulk Carrier rows, got {len(bulk_df)}"
    assert (bulk_df["ship_type"] == "Bulk Carrier").all()
    assert not bulk_df["turnaround_time_hours"].isnull().any()


def test_vessel_temporal_split_strict_inequality():
    loader = DataLoader()
    raw_vessel = loader.load_vessel_performance()
    bulk_df = VesselDatasetContract.validate_and_filter_bulk_carriers(raw_vessel)

    train_df, val_df, test_df = VesselDatasetContract.split_vessel_data_chronologically(bulk_df)

    assert len(train_df) == 463
    assert len(val_df) == 101
    assert len(test_df) == 105

    max_train = train_df["date"].max()
    min_val = val_df["date"].min()
    max_val = val_df["date"].max()
    min_test = test_df["date"].min()

    assert max_train < min_val, f"Temporal leakage: max(train) {max_train} >= min(val) {min_val}"
    assert max_val < min_test, f"Temporal leakage: max(val) {max_val} >= min(test) {min_test}"


def test_vessel_features_12_contract():
    assert len(VESSEL_FEATURES_12) == 12
    assert len(VESSEL_CATEGORICAL_FEATURES) == 4
    assert len(VESSEL_NUMERIC_FEATURES) == 8
    assert "turnaround_time_hours" not in VESSEL_FEATURES_12
    assert "delay_risk" not in VESSEL_FEATURES_12


def test_vessel_delay_risk_threshold_and_leakage_control():
    loader = DataLoader()
    raw_vessel = loader.load_vessel_performance()
    bulk_df = VesselDatasetContract.validate_and_filter_bulk_carriers(raw_vessel)

    bulk_df["delay_risk"] = (bulk_df["turnaround_time_hours"] > DELAY_RISK_THRESHOLD_HOURS).astype(int)
    assert DELAY_RISK_THRESHOLD_HOURS == 50.0

    # Ensure target is not in X features
    assert "turnaround_time_hours" not in VESSEL_FEATURES_12
    assert "delay_risk" not in VESSEL_FEATURES_12


# ---------------------------------------------------------------------------
# 2. Port Congestion Contract & Leakage Tests
# ---------------------------------------------------------------------------
def test_port_congestion_audit_india_port_absence():
    loader = DataLoader()
    raw_port = loader.load_port_congestion()

    audit_res = PortCongestionContract.audit_india_port_absence(raw_port)
    assert audit_res["total_rows"] == 6260
    assert audit_res["has_india_ports"] is False
    assert audit_res["data_scope"] == "GLOBAL_CONGESTION_PROXY"


def test_port_congestion_panel_lag_calculation_no_cross_port_leakage():
    """Addition 2: Verifies lag features are calculated strictly within each port entity."""
    loader = DataLoader()
    raw_port = loader.load_port_congestion()

    df_prep = PortCongestionContract.prepare_panel_dataset(raw_port)

    assert "congestion_index_lag1" in df_prep.columns
    assert "congestion_index_lead1" in df_prep.columns

    # Audit cross-port leakage
    assert PortCongestionContract.audit_no_cross_port_leakage(df_prep) is True


def test_port_congestion_temporal_split():
    loader = DataLoader()
    raw_port = loader.load_port_congestion()
    df_prep = PortCongestionContract.prepare_panel_dataset(raw_port)

    train_df, val_df, test_df = PortCongestionContract.split_congestion_data_chronologically(df_prep)

    assert train_df["week_start"].max() <= pd.to_datetime("2022-12-26")
    assert val_df["week_start"].min() >= pd.to_datetime("2023-01-02")
    assert val_df["week_start"].max() <= pd.to_datetime("2023-12-25")
    assert test_df["week_start"].min() >= pd.to_datetime("2024-01-01")


def test_port_congestion_lead1_target_definition():
    loader = DataLoader()
    raw_port = loader.load_port_congestion()
    df_prep = PortCongestionContract.prepare_panel_dataset(raw_port)

    assert "congestion_index_lead1" in df_prep.columns
    assert "high_congestion_risk_lead1" in df_prep.columns
    assert "congestion_index_lead1" not in PORT_CONGESTION_FEATURES
    assert "high_congestion_risk_lead1" not in PORT_CONGESTION_FEATURES


# ---------------------------------------------------------------------------
# 3. Model Training & Comparison Tests
# ---------------------------------------------------------------------------
def test_vessel_model_training_and_artifacts():
    res = train_and_evaluate_vessel_models(save_artifacts=True)

    assert "best_regression_model_name" in res
    assert "best_classification_model_name" in res
    assert os.path.exists(VESSEL_TURNAROUND_MODEL_PATH)
    assert os.path.exists(VESSEL_DELAY_RISK_MODEL_PATH)
    assert os.path.exists(VESSEL_COMPARISON_CSV_PATH)


def test_port_model_training_and_artifacts():
    res = train_and_evaluate_port_congestion_models(save_artifacts=True)

    assert "best_regressor_name" in res
    assert "best_classifier_name" in res
    assert os.path.exists(PORT_CONGESTION_REGRESSOR_PATH)
    assert os.path.exists(PORT_CONGESTION_CLASSIFIER_PATH)
    assert os.path.exists(PORT_COMPARISON_CSV_PATH)


def test_port_model_comparison_includes_addition1_metrics():
    """Addition 1: Confirms comparison CSV reports val_f1, val_precision, val_recall, val_roc_auc, val_pr_auc."""
    assert os.path.exists(PORT_COMPARISON_CSV_PATH)
    df_comp = pd.read_csv(PORT_COMPARISON_CSV_PATH)

    required_cols = [
        "model_name",
        "val_f1",
        "val_precision",
        "val_recall",
        "val_roc_auc",
        "val_pr_auc",
        "test_f1",
        "is_selected",
    ]
    for col in required_cols:
        assert col in df_comp.columns, f"Missing metric column '{col}' in port comparison CSV."


# ---------------------------------------------------------------------------
# 4. Production Service Tests
# ---------------------------------------------------------------------------
def test_vessel_service_single_predict_schema():
    service = VesselTurnaroundService()
    sample_input = get_sample_vessel_input()

    res = service.predict_turnaround(sample_input)

    assert res["model_name"] == "Vessel Turnaround & Delay Risk Model"
    assert isinstance(res["predicted_turnaround_hours"], float)
    assert res["predicted_turnaround_hours"] > 0
    assert isinstance(res["delay_risk_score"], float)
    assert res["delay_risk_level"] in ["Low", "High"]
    assert res["unit"] == "hours"


def test_port_service_single_predict_schema():
    service = PortCongestionService()
    sample_input = get_sample_port_input()

    res = service.predict_congestion(sample_input)

    assert res["model_name"] == "Global Port Congestion Risk Model"
    assert res["port"] == "Shanghai"
    assert isinstance(res["high_congestion_risk"], bool)
    assert isinstance(res["risk_probability"], float)
    assert res["data_scope"] in ("GLOBAL_CONGESTION_PROXY", "GLOBAL_CONGESTION_RISK")


def test_port_service_india_port_guard_raises():
    service = PortCongestionService()

    india_test_ports = ["Visakhapatnam", "Paradip", "Dhamra", "India_Port"]

    for port_name in india_test_ports:
        input_data = get_sample_port_input()
        input_data["port"] = port_name

        with pytest.raises(IndiaPortDataAbsentError, match="contains ZERO Indian ports"):
            service.predict_congestion(input_data)


def test_vessel_service_deterministic_inference():
    service = VesselTurnaroundService()
    sample_input = get_sample_vessel_input()

    res1 = service.predict_turnaround(sample_input)
    res2 = service.predict_turnaround(sample_input)

    assert res1["predicted_turnaround_hours"] == res2["predicted_turnaround_hours"]
    assert res1["delay_risk_score"] == res2["delay_risk_score"]


def test_port_service_deterministic_inference():
    service = PortCongestionService()
    sample_input = get_sample_port_input()

    res1 = service.predict_congestion(sample_input)
    res2 = service.predict_congestion(sample_input)

    assert res1["risk_probability"] == res2["risk_probability"]


# ---------------------------------------------------------------------------
# 5. Regression & Immutability Guards
# ---------------------------------------------------------------------------
def test_stage2_2c_selected_xgboost_model_unchanged():
    assert os.path.exists(DEFAULT_XGBOOST_MODEL_PATH)
    actual_hash = compute_file_sha256(DEFAULT_XGBOOST_MODEL_PATH)
    assert actual_hash == EXPECTED_XGBOOST_SHA256


def test_stage2_2c_comparison_file_unchanged():
    assert os.path.exists(STAGE2_2C_COMPARISON_CSV_PATH)
    df_comp = pd.read_csv(STAGE2_2C_COMPARISON_CSV_PATH)
    selected_row = df_comp[df_comp["is_selected"] == True]
    assert len(selected_row) == 1
    assert selected_row.iloc[0]["model"] == "Round 1 XGBoost"


def test_stage1_source_csvs_unchanged():
    loader = DataLoader()
    df_vessel = loader.load_vessel_performance()
    df_port = loader.load_port_congestion()

    assert len(df_vessel) == 2736
    assert len(df_port) == 6260
