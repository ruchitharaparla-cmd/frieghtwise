"""
Feature foundation and taxonomy definitions for FreightWise Round 2 Stages 2–6.
Provides feature taxonomy grouping and exact model feature extraction matching model.feature_names_in_.
"""

from typing import Dict, List, Optional, Any
import pandas as pd


FEATURE_GROUPS: Dict[str, List[str]] = {
    "temporal": ["month_num", "quarter", "month_sin", "month_cos", "year_month"],
    "freight_market": [
        "bulk_carrier_handysize_usd_day",
        "baltic_dry_index",
        "tanker_rate_aframax_usd_day",
        "supply_chain_pressure_index",
        "on_time_delivery_pct",
        "bdi_mom_change_pct",
        "container_yoy_pct",
    ],
    "commodity": [
        "thermal_coal_price",
        "corn",
        "palm_oil",
        "soybeans",
        "sugar",
        "wheat",
    ],
    "trade_import_demand": [
        "total_quantity",
        "shipment_count",
        "demand_share_pct",
        "demand_score",
        "route_priority",
        "Value_USD",
        "Value_INR",
    ],
    "vessel": [
        "speed_over_ground_knots",
        "engine_power_kw",
        "distance_traveled_nm",
        "draft_meters",
        "cargo_weight_tons",
        "average_load_percentage",
        "efficiency_nm_per_kwh",
        "seasonal_impact_score",
        "operational_cost_usd",
        "revenue_per_voyage_usd",
    ],
    "congestion": [
        "throughput_teu_mn",
        "vessels_at_anchor",
        "avg_wait_days",
        "congestion_index",
        "port_utilization_pct",
        "berth_delay_hrs",
    ],
    "geopolitical_disruption": [
        "brent_price",
        "wti_price",
        "dxy_index",
        "vix",
        "gpr_index",
        "brent_return",
        "wti_return",
        "brent_volatility_30d",
        "wti_volatility_30d",
        "brent_wti_spread",
        "event_severity",
        "event_flag",
    ],
}

FEATURE_TAXONOMY: Dict[str, List[str]] = {
    "RAW_FEATURES": [
        "baltic_dry_index",
        "brent_price",
        "wti_price",
        "dxy_index",
        "vix",
        "gpr_index",
        "thermal_coal_price",
        "speed_over_ground_knots",
        "engine_power_kw",
        "distance_traveled_nm",
        "draft_meters",
        "cargo_weight_tons",
        "average_load_percentage",
    ],
    "DERIVED_FEATURES": [
        "brent_return",
        "wti_return",
        "brent_wti_spread",
        "demand_share_pct",
        "demand_score",
        "congestion_index",
        "port_utilization_pct",
        "efficiency_nm_per_kwh",
    ],
    "LAG_FEATURES": [
        "freight_lag_1",
        "freight_lag_3",
        "freight_lag_6",
        "freight_lag_12",
        "baltic_dry_index_lag_1",
        "baltic_dry_index_lag_3",
        "brent_price_lag_1",
        "brent_price_lag_3",
        "wti_price_lag_1",
        "wti_price_lag_3",
        "dxy_index_lag_1",
        "dxy_index_lag_3",
        "vix_lag_1",
        "vix_lag_3",
        "gpr_index_lag_1",
        "gpr_index_lag_3",
        "thermal_coal_price_lag_1",
        "thermal_coal_price_lag_3",
    ],
    "ROLLING_FEATURES": [
        "freight_rolling_mean_3",
        "freight_rolling_mean_6",
        "freight_rolling_mean_12",
        "freight_rolling_std_3",
        "brent_volatility_7d",
        "brent_volatility_30d",
        "wti_volatility_7d",
        "wti_volatility_30d",
    ],
    "TARGETS": [
        "bulk_carrier_handysize_usd_day",
        "turnaround_time_hours",
        "operational_cost_usd",
    ],
    "MODEL_OUTPUTS": [
        "predicted_freight_usd_day",
        "freight_attractiveness_score",
        "predicted_turnaround_hours",
        "final_decision_score",
        "recommendation",
    ],
}


def extract_xgboost_model_features(df: pd.DataFrame, model: Any) -> pd.DataFrame:
    """
    Extracts and orders exact 26 input features from df matching model.feature_names_in_.
    Dynamically reads model.feature_names_in_ to guarantee exact feature ordering.
    Does NOT modify input df.
    """
    if not hasattr(model, "feature_names_in_"):
        raise AttributeError("Model object does not have 'feature_names_in_' attribute.")

    expected_features = list(model.feature_names_in_)

    missing = [f for f in expected_features if f not in df.columns]
    if missing:
        raise KeyError(f"DataFrame is missing required model input features: {missing}")

    # Return ordered copy
    return df[expected_features].copy()
