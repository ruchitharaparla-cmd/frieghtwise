"""
Explicit safe aggregation and join utilities for FreightWise Stage 1 Data Foundation.
Prevents many-to-many join explosions by explicitly aggregating daily/weekly datasets
to monthly temporal grain prior to joining with monthly freight data.
"""

import pandas as pd
from typing import Tuple


def aggregate_daily_oil_to_monthly(df_oil: pd.DataFrame) -> pd.DataFrame:
    """
    Safely aggregates daily oil & geopolitics data to monthly granularity.
    Computes monthly average prices, monthly volatility, and monthly max event severity.
    """
    df = df_oil.copy()
    if "year_month" not in df.columns:
        df["year_month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

    agg_dict = {
        "brent_price": ["mean", "last"],
        "wti_price": ["mean", "last"],
        "dxy_index": "mean",
        "vix": "mean",
        "gpr_index": "mean",
        "brent_volatility_30d": "mean",
        "wti_volatility_30d": "mean",
        "brent_wti_spread": "mean",
        "event_severity": "max",
        "event_flag": "max",
    }

    monthly_oil = df.groupby("year_month").agg(agg_dict)
    # Flatten MultiIndex columns
    monthly_oil.columns = ["_".join(col).strip() for col in monthly_oil.columns.values]
    monthly_oil = monthly_oil.reset_index()
    monthly_oil["canonical_month_start"] = monthly_oil["year_month"] + "-01"
    return monthly_oil


def aggregate_weekly_congestion_to_monthly(df_congestion: pd.DataFrame) -> pd.DataFrame:
    """
    Safely aggregates weekly port congestion data (global proxy) to monthly granularity per port/country/region.
    Prevents 4x fan-out join explosion when combining weekly congestion with monthly freight.
    """
    df = df_congestion.copy()
    if "year_month" not in df.columns:
        df["year_month"] = pd.to_datetime(df["week_start"]).dt.strftime("%Y-%m")

    agg_dict = {
        "throughput_teu_mn": "mean",
        "vessels_at_anchor": "mean",
        "avg_wait_days": "mean",
        "congestion_index": "mean",
        "port_utilization_pct": "mean",
        "berth_delay_hrs": "mean",
    }

    monthly_congestion = df.groupby(["year_month", "port", "country", "region"]).agg(agg_dict).reset_index()
    monthly_congestion["canonical_month_start"] = monthly_congestion["year_month"] + "-01"
    return monthly_congestion


def safe_join_monthly_freight_with_market(
    df_freight: pd.DataFrame, df_market_monthly: pd.DataFrame, join_key: str = "year_month"
) -> pd.DataFrame:
    """
    Performs a 1-to-1 safe join between monthly freight rates and monthly market indicators.
    Guards against row-multiplication fan-out explosions.
    """
    freight_len_before = len(df_freight)

    if join_key not in df_freight.columns or join_key not in df_market_monthly.columns:
        raise KeyError(f"Join key '{join_key}' must exist in both DataFrames")

    # Verify join_key uniqueness in right DataFrame
    if df_market_monthly[join_key].duplicated().any():
        raise ValueError(f"Right DataFrame contains duplicate values in join key '{join_key}'. Aggregation required.")

    merged = pd.merge(df_freight, df_market_monthly, on=join_key, how="inner", suffixes=("", "_market"))

    # Assert row count preservation (1-to-1 or subset join)
    if len(merged) > freight_len_before:
        raise ValueError(
            f"Many-to-many join explosion detected! Row count exploded from {freight_len_before} to {len(merged)}"
        )

    return merged
