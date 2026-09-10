"""Generate the exact 26 features expected by final_xgboost_model.joblib."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from .model_loader import load_xgboost_model
from .exogenous_forecast import (
    MARKET_COLUMNS,
    forecast_exogenous,
    load_monthly_exogenous,
)

TARGET = "bulk_carrier_handysize_usd_day"


def model_features() -> list[str]:
    """Use the checksum-verified production model as the feature source of truth."""
    model, _ = load_xgboost_model()
    names = list(model.feature_names_in_)
    if len(names) != 26:
        raise ValueError(f"Expected 26 model features, found {len(names)}.")
    return names


def _month_start(value) -> pd.Timestamp:
    return pd.Timestamp(value).to_period("M").to_timestamp()


def _feature_row(
    history: pd.DataFrame,
    target_month: pd.Timestamp,
    features: Sequence[str],
) -> pd.DataFrame:
    """Reproduce the original notebook lag/rolling/calendar formulas."""
    s = history[TARGET]
    row = {}

    # Original freight lag logic.
    for lag in (1, 3, 6, 12):
        row[f"freight_lag_{lag}"] = float(s.iloc[-lag])

    # Original rolling logic: target.shift(1).rolling(window).
    row["freight_rolling_mean_3"] = float(s.iloc[-3:].mean())
    row["freight_rolling_mean_6"] = float(s.iloc[-6:].mean())
    row["freight_rolling_mean_12"] = float(s.iloc[-12:].mean())
    row["freight_rolling_std_3"] = float(s.iloc[-3:].std(ddof=1))

    # Original market lag logic.
    for column in MARKET_COLUMNS:
        series = history[column]
        row[f"{column}_lag_1"] = float(series.iloc[-1])
        row[f"{column}_lag_3"] = float(series.iloc[-3])

    # Original calendar logic.
    month_num = target_month.month
    row["month_num"] = month_num
    row["quarter"] = target_month.quarter
    row["month_sin"] = np.sin(2 * np.pi * month_num / 12)
    row["month_cos"] = np.cos(2 * np.pi * month_num / 12)

    out = pd.DataFrame([row], columns=list(features))

    if out.shape != (1, 26):
        raise ValueError(f"Generated feature shape is {out.shape}, expected (1, 26).")
    if out.isna().any().any():
        raise ValueError("Generated feature vector contains NaN values.")

    return out


DEFAULT_PROCESSED_DIR = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "processed"
)


def generate_future_forecast(
    future_date,
    processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
) -> tuple[pd.DataFrame, float, dict]:
    """Generate exact 26-feature vector and forecast for a future date.

    The freight model is unchanged. Future freight values are generated
    recursively only because the original model requires target lags/rollings.
    """
    target_month = _month_start(future_date)
    model, model_version = load_xgboost_model()
    features = list(model.feature_names_in_)

    if len(features) != 26:
        raise ValueError("Serialized model does not expose exactly 26 features.")

    merged = load_monthly_exogenous(processed_dir)
    freight = merged[TARGET].dropna()
    if freight.empty:
        raise ValueError("No historical freight target values available.")

    last_freight_month = freight.index.max()
    if target_month <= last_freight_month:
        raise ValueError(
            f"{target_month.date()} is not a future freight date. "
            f"Latest observed freight month is {last_freight_month.date()}."
        )

    exog_result = forecast_exogenous(target_month, processed_dir)
    exog = exog_result.values

    # State contains observed freight followed by recursive forecasts.
    state = pd.DataFrame(index=exog.index)
    state[TARGET] = merged[TARGET].reindex(exog.index)
    for column in MARKET_COLUMNS:
        state[column] = exog[column]

    if state[TARGET].loc[:last_freight_month].isna().any():
        raise ValueError("Historical freight target contains missing months.")

    future_months = pd.date_range(
        last_freight_month + pd.offsets.MonthBegin(1),
        target_month,
        freq="MS",
    )

    for month in future_months:
        prior = state.loc[state.index < month].copy()

        if prior[TARGET].dropna().shape[0] < 12:
            raise ValueError("At least 12 prior freight observations are required.")

        # We require all market values used by lag-1/lag-3 to be present.
        recent_market = prior.loc[:, list(MARKET_COLUMNS)].iloc[-12:]
        if recent_market.isna().any().any():
            raise ValueError(
                f"Missing exogenous values before {month.date()}; "
                "refusing to fabricate features."
            )

        X_row = _feature_row(prior, month, features)
        prediction = float(model.predict(X_row)[0])

        if not np.isfinite(prediction):
            raise ValueError("XGBoost produced a non-finite forecast.")

        state.loc[month, TARGET] = prediction

    # For the requested month, features must only use information available
    # before that month.
    prior = state.loc[state.index < target_month].copy()
    X_final = _feature_row(prior, target_month, features).loc[:, features]

    forecast = float(model.predict(X_final)[0])

    metadata = {
        "requested_date": pd.Timestamp(future_date).date().isoformat(),
        "forecast_period": target_month.strftime("%Y-%m"),
        "latest_observed_freight_month": last_freight_month.strftime("%Y-%m"),
        "exogenous_methods": exog_result.methods,
        "exogenous_observed_through": exog_result.observed_through,
        "data_status": "FUTURE_FORECAST",
        "target": TARGET,
        "feature_count": 26,
        "model_version": model_version,
        "forecast_method": "RECURSIVE_XGBOOST_WITH_FORECAST_EXOGENOUS_INPUTS",
    }

    return X_final, forecast, metadata
