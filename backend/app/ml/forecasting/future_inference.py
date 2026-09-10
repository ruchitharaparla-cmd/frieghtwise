"""Public future freight forecasting interface."""

from __future__ import annotations

from pathlib import Path

from .future_features import (
    DEFAULT_PROCESSED_DIR,
    generate_future_forecast,
)


def forecast_future(
    future_date,
    processed_dir: str | Path = DEFAULT_PROCESSED_DIR,
) -> dict:
    """Accept a future date and return the future freight forecast."""
    X, predicted_rate, metadata = generate_future_forecast(
        future_date=future_date,
        processed_dir=processed_dir,
    )

    return {
        **metadata,
        "predicted_rate": predicted_rate,
        "unit": "USD/day",
        "currency": "USD",
        "model_name": "XGBoost",
        "feature_vector": {
            column: float(X.iloc[0][column])
            for column in X.columns
        },
    }
