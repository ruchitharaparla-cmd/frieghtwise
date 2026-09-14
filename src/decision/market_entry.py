from pathlib import Path

import numpy as np
import pandas as pd

from src.forecasting.future_inference import forecast_future


DATA_DIR = Path("data/processed")

FORECAST_FILE = DATA_DIR / "freight_forecast_predictions.csv"
RISK_FILE = DATA_DIR / "risk_idle_analysis.csv"

OUTPUT_FILE = DATA_DIR / "market_entry_analysis.csv"

# Generate the future decision-support horizon through this month.
FUTURE_END_DATE = pd.Timestamp("2027-03-01")


def load_data():
    forecast = pd.read_csv(FORECAST_FILE)
    forecast["date"] = pd.to_datetime(forecast["date"])

    risk = pd.read_csv(RISK_FILE)
    risk["date"] = pd.to_datetime(risk["date"])

    return forecast, risk


def generate_future_forecasts(
    historical_forecast: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate monthly future freight forecasts using the existing
    production XGBoost future-inference pipeline.

    The serialized XGBoost model is unchanged.
    """

    last_historical_date = (
        historical_forecast["date"].max()
    )

    future_dates = pd.date_range(
        last_historical_date
        + pd.offsets.MonthBegin(1),
        FUTURE_END_DATE,
        freq="MS",
    )

    if len(future_dates) == 0:
        return pd.DataFrame(
            columns=[
                "date",
                "predicted_freight_usd_day",
                "data_status",
                "model_name",
            ]
        )

    rows = []

    for date in future_dates:

        result = forecast_future(date)

        rows.append(
            {
                "date": pd.Timestamp(
                    date
                ),
                "predicted_freight_usd_day":
                    result["predicted_rate"],
                "data_status":
                    result["data_status"],
                "model_name":
                    result["model_name"],
            }
        )

    return pd.DataFrame(rows)


def build_combined_forecast(
    historical_forecast: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine historical freight forecasts with future XGBoost forecasts.
    """

    historical = historical_forecast.copy()

    historical["data_status"] = "HISTORICAL_FORECAST"
    historical["model_name"] = "XGBoost"

    future = generate_future_forecasts(
        historical
    )

    combined = pd.concat(
        [
            historical[
                [
                    "date",
                    "predicted_freight_usd_day",
                    "freight_attractiveness_score",
                    "data_status",
                    "model_name",
                ]
            ],
            future,
        ],
        ignore_index=True,
    )

    combined = (
        combined
        .sort_values("date")
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # Future forecasts don't have the historical
    # attractiveness score, so calculate it using
    # the same inverse-freight principle.
    if combined["freight_attractiveness_score"].isna().any():

        observed_scores = combined.loc[
            combined["freight_attractiveness_score"]
            .notna(),
            "freight_attractiveness_score",
        ]

        if not observed_scores.empty:

            min_score = observed_scores.min()
            max_score = observed_scores.max()

            future_mask = (
                combined["freight_attractiveness_score"]
                .isna()
            )

            future_rates = combined.loc[
                future_mask,
                "predicted_freight_usd_day",
            ]

            rate_min = (
                combined[
                    "predicted_freight_usd_day"
                ].min()
            )

            rate_max = (
                combined[
                    "predicted_freight_usd_day"
                ].max()
            )

            if rate_max > rate_min:

                normalized = (
                    rate_max - future_rates
                ) / (
                    rate_max - rate_min
                )

                combined.loc[
                    future_mask,
                    "freight_attractiveness_score",
                ] = (
                    min_score
                    + normalized
                    * (
                        max_score
                        - min_score
                    )
                )

    return combined


def calculate_market_signals(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = (
        df
        .sort_values("date")
        .copy()
    )

    # ---------------------------------------------------------
    # Future 3-month average
    # ---------------------------------------------------------

    df["forecast_3m_avg"] = (
        df["predicted_freight_usd_day"]
        .shift(-1)
        .rolling(3)
        .mean()
        .shift(-2)
    )

    # ---------------------------------------------------------
    # Future 6-month average
    # ---------------------------------------------------------

    df["forecast_6m_avg"] = (
        df["predicted_freight_usd_day"]
        .shift(-1)
        .rolling(6)
        .mean()
        .shift(-5)
    )

    current = (
        df["predicted_freight_usd_day"]
    )

    df["expected_change_3m_pct"] = (
        (
            df["forecast_3m_avg"]
            - current
        )
        / current
        * 100
    )

    df["expected_change_6m_pct"] = (
        (
            df["forecast_6m_avg"]
            - current
        )
        / current
        * 100
    )

    # Positive value means freight is expected
    # to become more expensive.
    df["market_pressure_score"] = np.clip(
        df["expected_change_3m_pct"] * 2
        + 50,
        0,
        100,
    )

    return df


def generate_entry_signal(row):
    """
    Generate market-entry guidance.

    Historical rows can use the corresponding risk data.

    Future rows do not have current risk observations,
    so the system does not falsely label them as low-risk
    charter opportunities.
    """

    attractiveness = (
        row["freight_attractiveness_score"]
    )

    change_3m = (
        row["expected_change_3m_pct"]
    )

    risk = row["overall_risk_score"]

    if pd.isna(change_3m):

        return "INSUFFICIENT DATA"

    # ---------------------------------------------------------
    # Risk unavailable for future forecast period.
    # ---------------------------------------------------------

    if pd.isna(risk):

        if (
            attractiveness >= 66
            and change_3m >= 5
        ):
            return "CAUTIOUS / REVIEW"

        if (
            attractiveness < 33
            and change_3m <= -5
        ):
            return "WAIT / MONITOR"

        return "PARTIAL / REVIEW"

    # ---------------------------------------------------------
    # Historical risk-aware signals.
    # ---------------------------------------------------------

    if (
        attractiveness >= 66
        and change_3m >= 5
        and risk < 66
    ):
        return "CHARTER NOW"

    if (
        attractiveness < 33
        and change_3m <= -5
        and risk < 66
    ):
        return "WAIT"

    if risk >= 66:

        return "CAUTIOUS / REVIEW"

    return "PARTIAL / REVIEW"


def contract_strategy(row):

    signal = (
        row["market_entry_signal"]
    )

    change_6m = (
        row["expected_change_6m_pct"]
    )

    if pd.isna(change_6m):

        return "INSUFFICIENT DATA"

    if signal == "CHARTER NOW":

        if change_6m >= 10:

            return (
                "CONSIDER MEDIUM-TERM CONTRACT"
            )

        return (
            "CONSIDER SHORT-TERM CONTRACT"
        )

    if signal == "WAIT":

        return (
            "DEFER CONTRACT / MONITOR MARKET"
        )

    if signal == "WAIT / MONITOR":

        return (
            "DEFER CONTRACT / MONITOR MARKET"
        )

    if signal == "CAUTIOUS / REVIEW":

        return (
            "SHORTER COMMITMENT / FLEXIBLE CONTRACT"
        )

    return (
        "COMPARE SPOT VS CONTRACT"
    )


def build_analysis():

    historical_forecast, risk = (
        load_data()
    )

    # ---------------------------------------------------------
    # 1. Historical + Future Freight Forecast
    # ---------------------------------------------------------

    df = build_combined_forecast(
        historical_forecast
    )

    # ---------------------------------------------------------
    # 2. Merge Risk / Idle Information
    # ---------------------------------------------------------

    risk_columns = [
        "date",
        "market_risk_score",
        "port_risk_score",
        "overall_risk_score",
        "risk_level",
        "idle_risk_score",
        "idle_risk_level",
    ]

    available_columns = [
        column
        for column in risk_columns
        if column in risk.columns
    ]

    df = df.merge(
        risk[available_columns],
        on="date",
        how="left",
    )

    # ---------------------------------------------------------
    # 3. Market Forecast Signals
    # ---------------------------------------------------------

    df = calculate_market_signals(
        df
    )

    # ---------------------------------------------------------
    # 4. Entry Decision
    # ---------------------------------------------------------

    df["market_entry_signal"] = (
        df.apply(
            generate_entry_signal,
            axis=1,
        )
    )

    # ---------------------------------------------------------
    # 5. Contract Strategy
    # ---------------------------------------------------------

    df["contract_strategy"] = (
        df.apply(
            contract_strategy,
            axis=1,
        )
    )

    return df


def main():

    result = build_analysis()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\nMarket Entry Engine completed."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        f"Rows: {len(result)}"
    )

    print(
        "\nLatest available analysis:"
    )

    print(
        result.tail(12).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
