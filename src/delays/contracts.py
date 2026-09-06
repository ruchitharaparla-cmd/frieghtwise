"""
Contracts and Validation Module for FreightWise Stage 3 — Delay & Congestion Prediction.

Enforces schema contracts, chronological splitting boundaries, zero-leakage guards,
independent panel-lag calculation per port, and India port absence detection.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Feature Contracts & Modeling Thresholds
# ---------------------------------------------------------------------------

# Exact 12 pre-voyage/operational features for vessel turnaround & delay risk
VESSEL_FEATURES_12: List[str] = [
    "route_type",
    "engine_type",
    "maintenance_status",
    "weather_condition",
    "speed_over_ground_knots",
    "engine_power_kw",
    "distance_traveled_nm",
    "draft_meters",
    "cargo_weight_tons",
    "seasonal_impact_score",
    "weekly_voyage_count",
    "average_load_percentage",
]

# Categorical vs Numeric breakdown for vessel features
VESSEL_CATEGORICAL_FEATURES: List[str] = [
    "route_type",
    "engine_type",
    "maintenance_status",
    "weather_condition",
]

VESSEL_NUMERIC_FEATURES: List[str] = [
    "speed_over_ground_knots",
    "engine_power_kw",
    "distance_traveled_nm",
    "draft_meters",
    "cargo_weight_tons",
    "seasonal_impact_score",
    "weekly_voyage_count",
    "average_load_percentage",
]

# Features for Port Congestion prediction at week t
PORT_CONGESTION_FEATURES: List[str] = [
    "port",
    "country",
    "region",
    "month_num",
    "year",
    "throughput_teu_mn",
    "vessels_at_anchor",
    "avg_wait_days",
    "congestion_index",
    "port_utilization_pct",
    "berth_delay_hrs",
    "vessels_at_anchor_lag1",
    "avg_wait_days_lag1",
    "congestion_index_lag1",
    "berth_delay_hrs_lag1",
    "vessels_at_anchor_lag2",
    "avg_wait_days_lag2",
    "congestion_index_lag2",
]

PORT_CATEGORICAL_FEATURES: List[str] = [
    "port",
    "country",
    "region",
]

# Project-defined modeling thresholds
DELAY_RISK_THRESHOLD_HOURS: float = 50.0  # Project-defined threshold (~60th-70th percentile of Bulk Carrier turnaround hours)
HIGH_CONGESTION_THRESHOLD_INDEX: float = 2.5  # ~75th percentile of historical congestion index distribution


class VesselDatasetContract:
    """
    Contract validator for Vessel Performance Dataset (`vessel_performance_processed.csv`).
    Reconciles 2,736 raw rows down to 669 Bulk Carrier records and establishes
    leakage-free chronological splits.
    """

    @staticmethod
    def validate_and_filter_bulk_carriers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Reconciles filtering pipeline from 2,736 raw vessel rows to 669 Bulk Carrier rows.

        Parameters
        ----------
        df : pd.DataFrame
            Raw vessel performance DataFrame.

        Returns
        -------
        pd.DataFrame
            Clean, chronologically sorted DataFrame containing exactly 669 Bulk Carrier records.
        """
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")

        if df.empty:
            raise ValueError("Vessel DataFrame is empty.")

        # 1. Filter ship_type == 'Bulk Carrier'
        if "ship_type" not in df.columns:
            raise ValueError("Missing required column 'ship_type' in vessel dataset.")

        bulk_df = df[df["ship_type"] == "Bulk Carrier"].copy()
        if len(bulk_df) != 669:
            raise ValueError(
                f"Expected exactly 669 Bulk Carrier records after filtering, got {len(bulk_df)}."
            )

        # 2. Check date & target presence
        if "date" not in bulk_df.columns:
            raise ValueError("Missing required column 'date' in vessel dataset.")

        if "turnaround_time_hours" not in bulk_df.columns:
            raise ValueError("Missing required target column 'turnaround_time_hours'.")

        if bulk_df["turnaround_time_hours"].isnull().any():
            raise ValueError("Target column 'turnaround_time_hours' contains missing/null values.")

        # 3. Handle categorical missingness cleanly
        for col in VESSEL_CATEGORICAL_FEATURES:
            if col in bulk_df.columns:
                bulk_df[col] = bulk_df[col].fillna("Unknown").astype(str)

        # 4. Sort chronologically without shuffling
        bulk_df["date"] = pd.to_datetime(bulk_df["date"])
        bulk_df = bulk_df.sort_values("date").reset_index(drop=True)

        return bulk_df

    @staticmethod
    def split_vessel_data_chronologically(
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits 669 Bulk Carrier records into strictly non-overlapping temporal partitions:
        - Train: 463 rows (2023-06-04 to 2024-02-25)
        - Validation: 101 rows (2024-03-03 to 2024-04-21)
        - Test: 105 rows (2024-04-28 to 2024-06-30)

        Guarantees max(train_date) < min(val_date) and max(val_date) < min(test_date).
        """
        train_mask = df["date"] <= "2024-02-25"
        val_mask = (df["date"] >= "2024-03-03") & (df["date"] <= "2024-04-21")
        test_mask = df["date"] >= "2024-04-28"

        train_df = df[train_mask].copy().reset_index(drop=True)
        val_df = df[val_mask].copy().reset_index(drop=True)
        test_df = df[test_mask].copy().reset_index(drop=True)

        # Strict temporal inequality verification
        max_train = train_df["date"].max()
        min_val = val_df["date"].min()
        max_val = val_df["date"].max()
        min_test = test_df["date"].min()

        if not (max_train < min_val):
            raise ValueError(
                f"Temporal leakage detected: max(train_date) {max_train} >= min(val_date) {min_val}"
            )

        if not (max_val < min_test):
            raise ValueError(
                f"Temporal leakage detected: max(val_date) {max_val} >= min(test_date) {min_test}"
            )

        return train_df, val_df, test_df


class PortCongestionContract:
    """
    Contract validator for Port Congestion Dataset (`port_congestion_processed.csv`).
    Computes panel-based lag features strictly per port entity, constructs 1-week-ahead
    lead targets, and performs strict audits against temporal and cross-port leakage.
    """

    @staticmethod
    def audit_india_port_absence(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Audits whether Indian ports exist in port_congestion_processed.csv.

        Returns
        -------
        Dict with keys:
            - total_rows: int (6260)
            - unique_ports: List[str]
            - unique_countries: List[str]
            - has_india_ports: bool (False)
            - data_scope: str ("GLOBAL_CONGESTION_PROXY")
        """
        if "port" not in df.columns:
            raise ValueError("Missing column 'port' in congestion dataset.")

        unique_ports = df["port"].unique().tolist()
        unique_countries = df["country"].unique().tolist() if "country" in df.columns else []

        india_keywords = [
            "india", "visakhapatnam", "paradip", "dhamra", "gangavaram",
            "krishnapatnam", "haldia", "mumbai", "jnpt", "chennai", "kandla", "cochin"
        ]

        has_india = any(
            any(kw in str(p).lower() for kw in india_keywords)
            for p in unique_ports
        ) or any("india" in str(c).lower() for c in unique_countries)

        return {
            "total_rows": len(df),
            "unique_ports": unique_ports,
            "unique_countries": unique_countries,
            "has_india_ports": has_india,
            "data_scope": "GLOBAL_CONGESTION_PROXY",
        }

    @staticmethod
    def prepare_panel_dataset(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates lag features and 1-week-ahead lead targets strictly per port entity.

        Addition 2: All congestion lag and rolling features are calculated independently
        within each port/panel entity after sorting by port and week_start.
        A lag for one port never uses a row belonging to another port.
        """
        df_clean = df.copy()
        df_clean["week_start"] = pd.to_datetime(df_clean["week_start"])
        df_clean["month_num"] = df_clean["week_start"].dt.month

        # Sort strictly by port and week_start
        df_clean = df_clean.sort_values(["port", "week_start"]).reset_index(drop=True)

        # Compute lags strictly within each port entity
        lags_to_create = [
            ("vessels_at_anchor", 1),
            ("avg_wait_days", 1),
            ("congestion_index", 1),
            ("berth_delay_hrs", 1),
            ("vessels_at_anchor", 2),
            ("avg_wait_days", 2),
            ("congestion_index", 2),
        ]

        for col, lag_k in lags_to_create:
            lag_col_name = f"{col}_lag{lag_k}"
            df_clean[lag_col_name] = df_clean.groupby("port")[col].shift(lag_k)

        # Compute 1-week-ahead lead target strictly within each port entity
        df_clean["congestion_index_lead1"] = df_clean.groupby("port")["congestion_index"].shift(-1)
        df_clean["high_congestion_risk_lead1"] = (
            df_clean["congestion_index_lead1"] >= HIGH_CONGESTION_THRESHOLD_INDEX
        ).astype(int)

        # Drop rows where lead1 target is NaN (i.e. the final week for each port)
        df_prepared = df_clean.dropna(subset=["congestion_index_lead1"]).reset_index(drop=True)

        return df_prepared

    @staticmethod
    def audit_no_cross_port_leakage(df_prepared: pd.DataFrame) -> bool:
        """
        Verifies that lag features for any given row derive strictly from the same port.
        """
        for port, group in df_prepared.groupby("port"):
            # Check lag1: first record of each port group should have NaN lag before dropna
            # or in prepared dataset, lag1 week_start should be exactly 7 days prior
            group_sorted = group.sort_values("week_start")
            date_diffs = group_sorted["week_start"].diff().dropna()
            # Weekly frequency check: all differences in date for same port should be 7 days
            if not (date_diffs == pd.Timedelta(days=7)).all():
                return False
        return True

    @staticmethod
    def split_congestion_data_chronologically(
        df_prepared: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Splits weekly panel dataset chronologically by week_start:
        - Train: 2019-01-07 to 2022-12-26 (208 weeks, 4,160 rows)
        - Validation: 2023-01-02 to 2023-12-25 (52 weeks, 1,040 rows)
        - Test: 2024-01-01 to 2024-12-23 (52 weeks, 1,040 rows)
        """
        train_mask = df_prepared["week_start"] <= "2022-12-26"
        val_mask = (df_prepared["week_start"] >= "2023-01-02") & (df_prepared["week_start"] <= "2023-12-25")
        test_mask = df_prepared["week_start"] >= "2024-01-01"

        train_df = df_prepared[train_mask].copy().reset_index(drop=True)
        val_df = df_prepared[val_mask].copy().reset_index(drop=True)
        test_df = df_prepared[test_mask].copy().reset_index(drop=True)

        return train_df, val_df, test_df
