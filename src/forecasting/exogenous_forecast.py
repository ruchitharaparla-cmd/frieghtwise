"""Fast forecasting of future monthly exogenous variables.

Source data:
- data/processed/freight_rates.csv
- data/processed/oil_geopolitics_processed.csv
- data/processed/commodity_prices_processed.csv

Method:
- Use observed monthly values whenever available.
- For the missing future tail, use a lightweight Ridge autoregression.
- Autoregression uses lags [1, 2, 3, 6, 12] plus:
    * linear trend
    * annual sine/cosine seasonality
- No interpolation or forward-filling of historical gaps.
- Internal historical gaps raise an error.
- Future values are explicitly marked as model forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Exact exogenous variables required by the original XGBoost model
# ---------------------------------------------------------------------

MARKET_COLUMNS = (
    "baltic_dry_index",
    "brent_price",
    "wti_price",
    "dxy_index",
    "vix",
    "gpr_index",
    "thermal_coal_price",
)

# Lags used by the lightweight exogenous forecasting model.
LAGS = (1, 2, 3, 6, 12)


# ---------------------------------------------------------------------
# Exceptions / result contract
# ---------------------------------------------------------------------

class FutureDataError(ValueError):
    """Raised when future forecasting cannot be performed safely."""


@dataclass(frozen=True)
class ExogenousForecastResult:
    """Result of future exogenous-variable forecasting."""

    values: pd.DataFrame
    methods: Dict[str, str]
    observed_through: Dict[str, str]


# ---------------------------------------------------------------------
# Date helper
# ---------------------------------------------------------------------

def _month_start(value) -> pd.Timestamp:
    """Convert any date-like value to the first day of its month."""
    return pd.Timestamp(value).to_period("M").to_timestamp()


# ---------------------------------------------------------------------
# Historical data validation
# ---------------------------------------------------------------------

def _check_monthly_series(
    series: pd.Series,
    name: str,
) -> pd.Series:
    """
    Validate one historical monthly time series.

    Requirements:
    - numeric
    - sorted
    - no duplicate months
    - no missing values
    - contiguous monthly dates
    """

    series = series.copy().astype(float)
    series = series.sort_index()

    # Duplicate dates are unsafe because lag calculations become ambiguous.
    if series.index.duplicated().any():
        raise FutureDataError(
            f"{name}: duplicate monthly timestamps found."
        )

    # We never fabricate internal historical values.
    if series.isna().any():
        missing = (
            series[series.isna()]
            .index
            .strftime("%Y-%m")
            .tolist()
        )

        raise FutureDataError(
            f"{name}: missing historical months found: "
            f"{missing[:12]}. "
            "Historical values will not be fabricated."
        )

    # Check that every month exists between first and last observation.
    expected_index = pd.date_range(
        series.index.min(),
        series.index.max(),
        freq="MS",
    )

    if not expected_index.equals(series.index):
        missing = (
            expected_index
            .difference(series.index)
            .strftime("%Y-%m")
            .tolist()
        )

        raise FutureDataError(
            f"{name}: historical monthly series is not contiguous. "
            f"Missing months: {missing[:12]}"
        )

    return series


# ---------------------------------------------------------------------
# Lightweight Ridge autoregressive forecasting
# ---------------------------------------------------------------------

def _ridge_ar_forecast(
    series: pd.Series,
    future_index: pd.DatetimeIndex,
    ridge_alpha: float = 1.0,
) -> np.ndarray:
    """
    Fast autoregressive forecast using NumPy.

    Features:
        intercept
        linear trend
        annual sine
        annual cosine
        lag 1
        lag 2
        lag 3
        lag 6
        lag 12

    This is intentionally lightweight so that forecasting seven
    exogenous variables remains fast.
    """

    y = series.to_numpy(dtype=float)

    # Need enough history to construct a 12-month lag.
    if len(y) < 24:
        return np.repeat(
            float(y[-1]),
            len(future_index),
        )

    rows = []
    targets = []

    # Start at 12 because lag_12 is required.
    for i in range(max(LAGS), len(y)):

        month = series.index[i].month

        row = [
            1.0,  # intercept
            float(i),  # linear trend

            # Annual seasonality
            np.sin(2 * np.pi * month / 12.0),
            np.cos(2 * np.pi * month / 12.0),
        ]

        # Historical autoregressive lags.
        row.extend(
            y[i - lag]
            for lag in LAGS
        )

        rows.append(row)
        targets.append(y[i])

    X = np.asarray(rows, dtype=float)
    target = np.asarray(targets, dtype=float)

    # -------------------------------------------------------------
    # Ridge regression:
    #
    # beta = (X'X + alpha I)^(-1) X'y
    #
    # Do not penalize the intercept.
    # -------------------------------------------------------------

    penalty = ridge_alpha * np.eye(X.shape[1])

    penalty[0, 0] = 0.0

    coefficients = np.linalg.solve(
        X.T @ X + penalty,
        X.T @ target,
    )

    # -------------------------------------------------------------
    # Recursive future forecasting
    # -------------------------------------------------------------

    history = list(y)
    forecasts = []

    for step, timestamp in enumerate(
        future_index,
        start=1,
    ):

        current_position = (
            len(y) + step - 1
        )

        month = timestamp.month

        row = np.array(
            [
                1.0,
                float(current_position),

                np.sin(
                    2 * np.pi * month / 12.0
                ),

                np.cos(
                    2 * np.pi * month / 12.0
                ),

                *[
                    history[-lag]
                    for lag in LAGS
                ],
            ],
            dtype=float,
        )

        prediction = float(
            row @ coefficients
        )

        if not np.isfinite(prediction):
            raise FutureDataError(
                "Exogenous autoregressive model "
                "produced a non-finite value."
            )

        history.append(prediction)
        forecasts.append(prediction)

    return np.asarray(
        forecasts,
        dtype=float,
    )


# ---------------------------------------------------------------------
# Forecast one variable
# ---------------------------------------------------------------------

def _forecast_one(
    series: pd.Series,
    target_end: pd.Timestamp,
    name: str,
) -> tuple[pd.Series, str]:
    """
    Extend one historical monthly series to target_end.

    Observed data remains unchanged.

    Only the future tail is forecast.
    """

    last_observed = series.index.max()

    # Nothing to forecast.
    if target_end <= last_observed:
        return (
            series.loc[:target_end],
            "OBSERVED",
        )

    future_index = pd.date_range(
        last_observed + pd.offsets.MonthBegin(1),
        target_end,
        freq="MS",
    )

    # Lightweight fallback when history is short.
    if len(series) < 24:

        predictions = np.repeat(
            float(series.iloc[-1]),
            len(future_index),
        )

        method = "PERSISTENCE_BASELINE"

    else:

        predictions = _ridge_ar_forecast(
            series=series,
            future_index=future_index,
        )

        method = "RIDGE_AR_12"

    if not np.isfinite(predictions).all():
        raise FutureDataError(
            f"{name}: forecast contains non-finite values."
        )

    future_series = pd.Series(
        predictions,
        index=future_index,
        name=name,
    )

    combined = pd.concat(
        [
            series,
            future_series,
        ]
    )

    return combined, method


# ---------------------------------------------------------------------
# Load and reproduce the original monthly data preparation
# ---------------------------------------------------------------------

def load_monthly_exogenous(
    processed_dir: str | Path = "data/processed",
) -> pd.DataFrame:
    """
    Reproduce the monthly data preparation used by the original
    Round-1 freight feature-engineering pipeline.

    Sources:
        freight_rates.csv
        oil_geopolitics_processed.csv
        commodity_prices_processed.csv

    Returns a monthly DataFrame containing:

        bulk_carrier_handysize_usd_day
        baltic_dry_index
        brent_price
        wti_price
        dxy_index
        vix
        gpr_index
        thermal_coal_price
    """

    processed_dir = Path(
        processed_dir
    )

    # -------------------------------------------------------------
    # Load datasets
    # -------------------------------------------------------------

    freight = pd.read_csv(
        processed_dir / "freight_rates.csv"
    )

    oil = pd.read_csv(
        processed_dir / "oil_geopolitics_processed.csv"
    )

    commodity = pd.read_csv(
        processed_dir / "commodity_prices_processed.csv"
    )

    # -------------------------------------------------------------
    # Convert dates
    # -------------------------------------------------------------

    freight["date"] = pd.to_datetime(
        freight["date"],
        errors="coerce",
    )

    oil["date"] = pd.to_datetime(
        oil["date"],
        errors="coerce",
    )

    commodity["date"] = pd.to_datetime(
        commodity["date"],
        errors="coerce",
    )

    # -------------------------------------------------------------
    # Validate dates
    # -------------------------------------------------------------

    if freight["date"].isna().any():
        raise FutureDataError(
            "freight_rates.csv contains invalid dates."
        )

    if oil["date"].isna().any():
        raise FutureDataError(
            "oil_geopolitics_processed.csv "
            "contains invalid dates."
        )

    if commodity["date"].isna().any():
        raise FutureDataError(
            "commodity_prices_processed.csv "
            "contains invalid dates."
        )

    # -------------------------------------------------------------
    # Freight monthly dataset
    #
    # The original freight data is already monthly.
    # -------------------------------------------------------------

    required_freight_columns = [
        "date",
        "bulk_carrier_handysize_usd_day",
        "baltic_dry_index",
    ]

    missing = [
        column
        for column in required_freight_columns
        if column not in freight.columns
    ]

    if missing:
        raise FutureDataError(
            "freight_rates.csv is missing columns: "
            f"{missing}"
        )

    freight_m = (
        freight[
            required_freight_columns
        ]
        .assign(
            year_month=lambda x:
                x["date"].dt.to_period("M")
        )
        .sort_values("date")
        .drop_duplicates(
            "year_month",
            keep="last",
        )
        .set_index("year_month")
    )

    # -------------------------------------------------------------
    # Oil / macro monthly aggregation
    #
    # Original feature engineering uses monthly mean values.
    # -------------------------------------------------------------

    required_oil_columns = [
        "brent_price",
        "wti_price",
        "dxy_index",
        "vix",
        "gpr_index",
    ]

    missing = [
        column
        for column in required_oil_columns
        if column not in oil.columns
    ]

    if missing:
        raise FutureDataError(
            "oil_geopolitics_processed.csv is missing "
            f"columns: {missing}"
        )

    oil_m = (
        oil
        .assign(
            year_month=lambda x:
                x["date"].dt.to_period("M")
        )
        .groupby("year_month")
        .agg(
            {
                "brent_price": "mean",
                "wti_price": "mean",
                "dxy_index": "mean",
                "vix": "mean",
                "gpr_index": "mean",
            }
        )
    )

    # -------------------------------------------------------------
    # Thermal Coal Newcastle
    #
    # IMPORTANT:
    # Do not automatically replace this with another coal concept.
    # -------------------------------------------------------------

    if "commodity" not in commodity.columns:
        raise FutureDataError(
            "commodity_prices_processed.csv does not "
            "contain the 'commodity' column."
        )

    if "average_price" not in commodity.columns:
        raise FutureDataError(
            "commodity_prices_processed.csv does not "
            "contain the 'average_price' column."
        )

    coal = commodity[
        commodity["commodity"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("thermal coal newcastle")
    ].copy()

    if coal.empty:

        possible_matches = (
            commodity[
                commodity["commodity"]
                .astype(str)
                .str.contains(
                    "thermal.*coal|coal.*newcastle",
                    case=False,
                    regex=True,
                    na=False,
                )
            ]["commodity"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        raise FutureDataError(
            "No exact 'Thermal Coal Newcastle' "
            "commodity series found. "
            f"Possible matches: {possible_matches}. "
            "Refusing to substitute a different "
            "commodity concept."
        )

    coal_m = (
        coal
        .assign(
            year_month=lambda x:
                x["date"].dt.to_period("M")
        )
        .groupby("year_month")[
            "average_price"
        ]
        .mean()
        .rename(
            "thermal_coal_price"
        )
        .to_frame()
    )

    # -------------------------------------------------------------
    # Merge all monthly datasets
    # -------------------------------------------------------------

    merged = (
        freight_m
        .join(
            oil_m,
            how="left",
        )
        .join(
            coal_m,
            how="left",
        )
    )

    merged.index = (
        merged.index
        .to_timestamp()
    )

    merged = merged.sort_index()

    # -------------------------------------------------------------
    # Validate required output columns
    # -------------------------------------------------------------

    required_columns = [
        *MARKET_COLUMNS,
        "bulk_carrier_handysize_usd_day",
    ]

    missing = [
        column
        for column in required_columns
        if column not in merged.columns
    ]

    if missing:
        raise FutureDataError(
            "Required columns missing after monthly merge: "
            f"{missing}"
        )

    return merged


# ---------------------------------------------------------------------
# Public exogenous forecasting function
# ---------------------------------------------------------------------

def forecast_exogenous(
    target_date,
    processed_dir: str | Path = "data/processed",
) -> ExogenousForecastResult:
    """
    Forecast all required exogenous variables through target month.

    IMPORTANT:
    The common output starts at the latest historical start date
    among all required variables.

    In the current data:
        BDI starts around 2000-01
        Oil/macro starts around 2010-02
        Thermal coal starts around 2010-01

    Therefore the common feature period starts around 2010-02.

    No missing 2000-2010 oil/macro values are fabricated.
    """

    target_month = _month_start(
        target_date
    )

    # Load original monthly data.
    df = load_monthly_exogenous(
        processed_dir
    )

    # -------------------------------------------------------------
    # Find the first month where ALL required exogenous variables
    # have an observed value.
    # -------------------------------------------------------------

    starts = []

    for column in MARKET_COLUMNS:

        observed = (
            df[column]
            .dropna()
        )

        if observed.empty:
            raise FutureDataError(
                f"{column}: no observed history available."
            )

        starts.append(
            observed.index.min()
        )

    common_start = max(starts)

    # -------------------------------------------------------------
    # Create common monthly timeline.
    # -------------------------------------------------------------

    output = pd.DataFrame(
        index=pd.date_range(
            common_start,
            target_month,
            freq="MS",
        )
    )

    methods: Dict[str, str] = {}
    observed_through: Dict[str, str] = {}

    # -------------------------------------------------------------
    # Forecast each exogenous variable.
    # -------------------------------------------------------------

    for column in MARKET_COLUMNS:

        raw = (
            df[column]
            .dropna()
        )

        # Validate its own historical period.
        raw = _check_monthly_series(
            raw,
            column,
        )

        series, method = _forecast_one(
            series=raw,
            target_end=target_month,
            name=column,
        )

        # Align only to the valid common timeline.
        output[column] = (
            series
            .reindex(output.index)
        )

        methods[column] = method

        observed_through[column] = (
            raw.index.max()
            .strftime("%Y-%m-%d")
        )

    # -------------------------------------------------------------
    # Final safety check.
    #
    # We NEVER silently fill missing values.
    # -------------------------------------------------------------

    missing_counts = (
        output[
            list(MARKET_COLUMNS)
        ]
        .isna()
        .sum()
    )

    if missing_counts.any():

        missing_info = {
            column: int(count)
            for column, count
            in missing_counts.items()
            if count > 0
        }

        raise FutureDataError(
            "Exogenous forecast contains missing values: "
            f"{missing_info}"
        )

    return ExogenousForecastResult(
        values=output,
        methods=methods,
        observed_through=observed_through,
    )