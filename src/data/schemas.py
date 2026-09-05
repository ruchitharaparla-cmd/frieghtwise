"""
Schema contract definitions for FreightWise Round 2 — Stage 1 datasets.
Treats dataset schemas and model input schemas as separate contracts.
"""

from typing import List, Dict, Any, Optional
import pandas as pd


class FreightDatasetSchema:
    """
    Contract for the 46-column freight_model_features.csv processed dataset.
    """
    EXPECTED_COLUMN_COUNT = 46
    REQUIRED_COLUMNS: List[str] = [
        "date",
        "bulk_carrier_handysize_usd_day",
        "baltic_dry_index",
        "tanker_rate_aframax_usd_day",
        "supply_chain_pressure_index",
        "on_time_delivery_pct",
        "bdi_mom_change_pct",
        "container_yoy_pct",
        "year_month",
        "brent_price",
        "wti_price",
        "dxy_index",
        "vix",
        "gpr_index",
        "brent_volatility_30d",
        "wti_volatility_30d",
        "brent_wti_spread",
        "event_severity",
        "event_flag",
        "thermal_coal_price",
        "freight_lag_1",
        "freight_lag_3",
        "freight_lag_6",
        "freight_lag_12",
        "freight_rolling_mean_3",
        "freight_rolling_mean_6",
        "freight_rolling_mean_12",
        "freight_rolling_std_3",
        "month_num",
        "quarter",
        "month_sin",
        "month_cos",
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
    ]

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        missing = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Freight dataset schema missing required columns: {missing}")
        if len(df.columns) < cls.EXPECTED_COLUMN_COUNT:
            raise ValueError(
                f"Freight dataset schema expected at least {cls.EXPECTED_COLUMN_COUNT} columns, got {len(df.columns)}"
            )
        return True


class FreightModelInputSchema:
    """
    Contract for the 26-feature input schema expected by final_xgboost_model.joblib.
    Features and ordering must match model.feature_names_in_ dynamically.
    """
    DEFAULT_26_FEATURES: List[str] = [
        "freight_lag_1",
        "freight_lag_3",
        "freight_lag_6",
        "freight_lag_12",
        "freight_rolling_mean_3",
        "freight_rolling_mean_6",
        "freight_rolling_mean_12",
        "freight_rolling_std_3",
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
        "month_num",
        "quarter",
        "month_sin",
        "month_cos",
    ]

    @classmethod
    def validate(cls, df: pd.DataFrame, expected_features: Optional[List[str]] = None) -> bool:
        features = expected_features or cls.DEFAULT_26_FEATURES
        missing = [f for f in features if f not in df.columns]
        if missing:
            raise ValueError(f"Model input schema missing required feature columns: {missing}")
        return True


class VesselPerformanceSchema:
    """
    Contract for vessel_performance_processed.csv dataset (20 columns).
    """
    REQUIRED_COLUMNS: List[str] = [
        "date",
        "ship_type",
        "route_type",
        "engine_type",
        "maintenance_status",
        "speed_over_ground_knots",
        "engine_power_kw",
        "distance_traveled_nm",
        "draft_meters",
        "weather_condition",
        "cargo_weight_tons",
        "operational_cost_usd",
        "revenue_per_voyage_usd",
        "turnaround_time_hours",
        "efficiency_nm_per_kwh",
        "seasonal_impact_score",
        "weekly_voyage_count",
        "average_load_percentage",
    ]

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        missing = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Vessel performance schema missing required columns: {missing}")
        return True


class IndiaBulkImportsSchema:
    """
    Contract for india_bulk_imports_2022_2026.csv dataset (10 columns).
    """
    REQUIRED_COLUMNS: List[str] = [
        "Year",
        "Period_Start",
        "Period_End",
        "Commodity",
        "Country_of_Consignment",
        "Port",
        "Unit",
        "Quantity",
        "Value_INR",
        "Value_USD",
    ]

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        missing = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"India bulk imports schema missing required columns: {missing}")
        # Validate unit is TON
        invalid_units = df[df["Unit"] != "TON"]
        if not invalid_units.empty:
            raise ValueError(f"India bulk imports schema found non-TON units: {invalid_units['Unit'].unique()}")
        return True


class PortCongestionSchema:
    """
    Contract for port_congestion_processed.csv dataset (12 columns).
    Global proxy dataset with 0 Indian ports.
    """
    REQUIRED_COLUMNS: List[str] = [
        "week_start",
        "year",
        "month",
        "port",
        "country",
        "region",
        "throughput_teu_mn",
        "vessels_at_anchor",
        "avg_wait_days",
        "congestion_index",
        "port_utilization_pct",
        "berth_delay_hrs",
    ]

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        missing = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Port congestion schema missing required columns: {missing}")
        return True
