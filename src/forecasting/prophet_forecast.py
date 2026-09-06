"""
Prophet Forecasting Benchmark for FreightWise Round 2 — Stage 2.3.

Provides an isolated, reproducible Prophet forecasting implementation.

Constraints:
  - Univariate target-only benchmark: ds = date, y = bulk_carrier_handysize_usd_day.
  - Strictly no external regressors in this baseline benchmark.
  - Monthly frequency ('MS').
  - Strict chronological isolation:
      Validation forecast: fits on training period only (143 observations, 2011-02-01 to 2022-12-01).
      Test forecast: fits on train + validation periods (155 observations, 2011-02-01 to 2023-12-01).
      The 2024 test set is NEVER used for fitting, tuning, or hyperparameter selection.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .contracts import DEFAULT_DATE_COL, DEFAULT_TARGET_COL
from .metrics import calculate_all_metrics
from .split import chronological_train_val_test_split

logger = logging.getLogger(__name__)

# Check package availability gracefully
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    Prophet = None
    PROPHET_AVAILABLE = False

PROPHET_PREDICTIONS_CSV_PATH: str = "data/processed/prophet_forecast_predictions.csv"


class ProphetForecaster:
    """
    Univariate Prophet forecaster adhering strictly to FreightWise evaluation contracts.
    """

    def __init__(self, **prophet_kwargs):
        """
        Initialize ProphetForecaster.

        Parameters
        ----------
        **prophet_kwargs : optional kwargs passed to Prophet constructor.
        """
        if not PROPHET_AVAILABLE:
            raise ImportError(
                "prophet package is not available in the current environment. "
                "Install with 'pip install prophet' to enable Prophet forecasting."
            )
        self.prophet_kwargs = prophet_kwargs
        self.model: Optional[Any] = None

    def fit_and_forecast(
        self,
        history_df: pd.DataFrame,
        horizon: int = 12,
        target_col: str = DEFAULT_TARGET_COL,
        date_col: str = DEFAULT_DATE_COL,
        freq: str = "MS",
    ) -> pd.DataFrame:
        """
        Fits a univariate Prophet model on historical data and forecasts the specified horizon.

        Parameters
        ----------
        history_df : pd.DataFrame
            Historical DataFrame containing `date_col` and `target_col`.
        horizon : int
            Forecast horizon in steps (default 12 months).
        target_col : str
            Target freight column name.
        date_col : str
            Date column name.
        freq : str
            Frequency string ('MS' for month start).

        Returns
        -------
        pd.DataFrame
            DataFrame with columns ['date', 'predicted'] aligned to the forecast horizon.
        """
        if not PROPHET_AVAILABLE:
            raise ImportError("Prophet is not installed in the environment.")

        if target_col not in history_df.columns:
            raise KeyError(f"Target column '{target_col}' not found in input history.")
        if date_col not in history_df.columns:
            raise KeyError(f"Date column '{date_col}' not found in input history.")

        # Prepare ds / y DataFrame
        prophet_df = pd.DataFrame({
            "ds": pd.to_datetime(history_df[date_col]),
            "y": history_df[target_col].astype(float),
        }).sort_values("ds").reset_index(drop=True)

        # Fit model on historical data only
        # Suppress verbose logging from cmdstanpy
        model = Prophet(**self.prophet_kwargs)
        model.fit(prophet_df)
        self.model = model

        # Generate future dates
        future_df = model.make_future_dataframe(periods=horizon, freq=freq, include_history=False)
        forecast_df = model.predict(future_df)

        result_df = pd.DataFrame({
            "date": forecast_df["ds"].dt.strftime("%Y-%m-%d").values[:horizon],
            "predicted": forecast_df["yhat"].values[:horizon].astype(np.float64),
        })

        return result_df


def run_prophet_benchmark(
    loader: Optional[Any] = None,
    save_csv: bool = True,
    output_path: str = PROPHET_PREDICTIONS_CSV_PATH,
    forecaster_cls: Any = ProphetForecaster,
) -> Dict[str, Any]:
    """
    Executes the Prophet benchmark for FreightWise Stage 2.3.

    Strict chronological isolation:
      - Validation forecast (2023): fits on training partition (143 observations, 2011-02-01 to 2022-12-01).
      - Test forecast (2024): fits on train + validation partitions (155 observations, 2011-02-01 to 2023-12-01).
      - Zero 2024 test data is used for model fitting or tuning.

    Parameters
    ----------
    loader : optional DataLoader
    save_csv : bool
    output_path : str
    forecaster_cls : Forecaster class (can be injected for testing/mocking)

    Returns
    -------
    Dict containing validation metrics, test metrics, prediction DataFrame, and dates.
    """
    if not PROPHET_AVAILABLE and forecaster_cls is ProphetForecaster:
        raise ImportError("Prophet is not available. Please install prophet.")

    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()

    df_full = loader.load_freight_model_features()
    split_res = chronological_train_val_test_split(df_full, date_col=DEFAULT_DATE_COL)

    train_df = split_res.train
    val_df = split_res.validation
    test_df = split_res.test

    assert len(train_df) == 143, f"Expected 143 train rows, got {len(train_df)}"
    assert len(val_df) == 12, f"Expected 12 val rows, got {len(val_df)}"
    assert len(test_df) == 12, f"Expected 12 test rows, got {len(test_df)}"

    # 1. Validation Forecast: fit on train_df only
    val_forecaster = forecaster_cls()
    val_fc = val_forecaster.fit_and_forecast(
        history_df=train_df[[DEFAULT_DATE_COL, DEFAULT_TARGET_COL]],
        horizon=len(val_df),
        target_col=DEFAULT_TARGET_COL,
        date_col=DEFAULT_DATE_COL,
    )

    # 2. Test Forecast: fit on train_df + val_df
    # Strict isolation: 2024 test data is NOT present in history_for_test
    history_for_test = pd.concat([train_df, val_df], ignore_index=True)
    test_forecaster = forecaster_cls()
    test_fc = test_forecaster.fit_and_forecast(
        history_df=history_for_test[[DEFAULT_DATE_COL, DEFAULT_TARGET_COL]],
        horizon=len(test_df),
        target_col=DEFAULT_TARGET_COL,
        date_col=DEFAULT_DATE_COL,
    )

    # Align with actual targets
    y_val_actual = val_df[DEFAULT_TARGET_COL].values
    y_val_pred = val_fc["predicted"].values
    val_metrics = calculate_all_metrics(y_val_actual, y_val_pred)

    y_test_actual = test_df[DEFAULT_TARGET_COL].values
    y_test_pred = test_fc["predicted"].values
    test_metrics = calculate_all_metrics(y_test_actual, y_test_pred)

    # Format predictions DataFrame
    val_pred_rows = pd.DataFrame({
        "date": val_fc["date"].values,
        "actual": y_val_actual,
        "predicted": y_val_pred,
        "model": "Prophet",
        "split": "validation",
    })

    test_pred_rows = pd.DataFrame({
        "date": test_fc["date"].values,
        "actual": y_test_actual,
        "predicted": y_test_pred,
        "model": "Prophet",
        "split": "test",
    })

    predictions_df = pd.concat([val_pred_rows, test_pred_rows], ignore_index=True)

    if save_csv:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        predictions_df.to_csv(output_path, index=False)

    return {
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "predictions_df": predictions_df,
        "val_dates": val_fc["date"].tolist(),
        "test_dates": test_fc["date"].tolist(),
    }
