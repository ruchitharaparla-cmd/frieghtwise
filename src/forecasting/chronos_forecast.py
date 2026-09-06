"""
Chronos-2 Forecasting Adapter for FreightWise Round 2 — Stage 2.3.

Provides a decoupled adapter for zero-shot time-series forecasting using
amazon/chronos-2.

Constraints:
  - Zero-shot inference only — strictly NO fine-tuning.
  - Univariate target-only benchmark: bulk_carrier_handysize_usd_day.
  - Monthly frequency ('MS').
  - 12-month forecast horizon for validation (2023) and test (2024).
  - Zero temporal target leakage:
      Validation forecast: uses strictly train history (143 observations, 2011-02-01 to 2022-12-01).
      Test forecast: uses history through validation (155 observations, 2011-02-01 to 2023-12-01).
      No 2024 observations are ever passed to model inference or conditioning for the test forecast.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .contracts import DEFAULT_DATE_COL, DEFAULT_TARGET_COL
from .metrics import calculate_all_metrics
from .split import chronological_train_val_test_split

logger = logging.getLogger(__name__)

# Check package availability gracefully
try:
    from chronos import Chronos2Pipeline
    CHRONOS_AVAILABLE = True
except ImportError:
    Chronos2Pipeline = None
    CHRONOS_AVAILABLE = False

CHRONOS_PREDICTIONS_CSV_PATH: str = "data/processed/chronos2_forecast_predictions.csv"
CHRONOS_MODEL_ID: str = "amazon/chronos-2"

# Singleton cache for pipeline to prevent redundant loads and downloads
_CACHED_PIPELINE: Optional[Any] = None


class ChronosAdapter:
    """
    Decoupled adapter wrapping Chronos-2 zero-shot pipeline.
    Shields the rest of FreightWise from direct dependency on chronos internals.
    """

    def __init__(
        self,
        model_id: str = CHRONOS_MODEL_ID,
        device_map: str = "cpu",
        pipeline: Optional[Any] = None,
    ):
        """
        Initialize the ChronosAdapter.

        Parameters
        ----------
        model_id : str
            Hugging Face model identifier or local path.
        device_map : str
            Device to map the pipeline ('cpu' or 'cuda').
        pipeline : optional pre-loaded Chronos2Pipeline (useful for mocking/testing).
        """
        if not CHRONOS_AVAILABLE and pipeline is None:
            raise ImportError(
                "chronos package is not available in the current environment. "
                "Install with 'pip install chronos-forecasting' to enable Chronos-2."
            )
        self.model_id = model_id
        self.device_map = device_map
        self._pipeline = pipeline

    def load_model(self) -> Any:
        """
        Loads the Chronos2Pipeline. Reuses the in-memory singleton if available.
        Attempts to load from local cache first to prevent repeated internet requests.
        """
        global _CACHED_PIPELINE
        if self._pipeline is not None:
            return self._pipeline

        if _CACHED_PIPELINE is not None:
            self._pipeline = _CACHED_PIPELINE
            return self._pipeline

        if not CHRONOS_AVAILABLE:
            raise ImportError("Chronos is not installed in the environment.")

        logger.info(f"Loading Chronos-2 pipeline ({self.model_id})...")
        try:
            # First attempt loading with local files only if cached
            pipeline = Chronos2Pipeline.from_pretrained(
                self.model_id,
                device_map=self.device_map,
                local_files_only=True,
            )
        except Exception:
            # Fall back to standard load (which uses local cache if present)
            pipeline = Chronos2Pipeline.from_pretrained(
                self.model_id,
                device_map=self.device_map,
            )

        _CACHED_PIPELINE = pipeline
        self._pipeline = pipeline
        return self._pipeline

    def forecast(
        self,
        history_df: pd.DataFrame,
        horizon: int = 12,
        target_col: str = DEFAULT_TARGET_COL,
        date_col: str = DEFAULT_DATE_COL,
        freq: str = "MS",
    ) -> pd.DataFrame:
        """
        Generates zero-shot point forecasts for the specified horizon using historical target.

        Parameters
        ----------
        history_df : pd.DataFrame
            Historical observations containing at least `date_col` and `target_col`.
        horizon : int
            Forecast horizon in steps (default 12 months).
        target_col : str
            Target column name.
        date_col : str
            Date column name.
        freq : str
            Pandas frequency string ('MS' for month start).

        Returns
        -------
        pd.DataFrame
            DataFrame with columns ['date', 'predicted'] aligned to the forecast horizon.
        """
        pipeline = self.load_model()

        if target_col not in history_df.columns:
            raise KeyError(f"Target column '{target_col}' not found in input history.")
        if date_col not in history_df.columns:
            raise KeyError(f"Date column '{date_col}' not found in input history.")

        # Ensure history is sorted chronologically
        sorted_history = history_df.sort_values(by=date_col).copy().reset_index(drop=True)
        sorted_history[date_col] = pd.to_datetime(sorted_history[date_col])

        # Prepare input for predict_df: item_id, timestamp, target
        input_df = pd.DataFrame({
            "item_id": "freight_target",
            "timestamp": sorted_history[date_col],
            "target": sorted_history[target_col].astype(float),
        })

        # Generate future forecast using predict_df with median quantile (0.50)
        fc_df = pipeline.predict_df(
            df=input_df,
            prediction_length=horizon,
            quantile_levels=[0.5],
            id_column="item_id",
            timestamp_column="timestamp",
            target="target",
        )

        # Extract predictions column (named 'predictions' or '0.5')
        pred_col = "predictions" if "predictions" in fc_df.columns else "0.5"
        predictions = fc_df[pred_col].values[:horizon]

        # Calculate exact future dates from the last history date
        last_date = sorted_history[date_col].iloc[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.MonthBegin(1),
            periods=horizon,
            freq=freq,
        )

        result_df = pd.DataFrame({
            "date": future_dates.strftime("%Y-%m-%d"),
            "predicted": np.asarray(predictions, dtype=np.float64),
        })

        return result_df


def run_chronos_benchmark(
    loader: Optional[Any] = None,
    save_csv: bool = True,
    output_path: str = CHRONOS_PREDICTIONS_CSV_PATH,
    adapter: Optional[ChronosAdapter] = None,
) -> Dict[str, Any]:
    """
    Executes the Chronos-2 zero-shot benchmark for FreightWise Stage 2.3.

    Strict chronological isolation:
      - Validation forecast (2023): conditioned ONLY on training partition (first 143 observations).
      - Test forecast (2024): conditioned ONLY on train + validation partitions (first 155 observations).
      - Zero 2024 test data is used for model conditioning, fitting, or tuning.

    Parameters
    ----------
    loader : optional DataLoader
    save_csv : bool
    output_path : str
    adapter : optional ChronosAdapter

    Returns
    -------
    Dict containing validation metrics, test metrics, prediction DataFrame, and dates.
    """
    if not CHRONOS_AVAILABLE and adapter is None:
        raise ImportError(
            "Chronos is not available. Please install chronos-forecasting."
        )

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

    if adapter is None:
        adapter = ChronosAdapter()

    # 1. Validation Forecast: conditioned strictly on train_df (first 143 rows)
    val_fc = adapter.forecast(
        history_df=train_df[[DEFAULT_DATE_COL, DEFAULT_TARGET_COL]],
        horizon=len(val_df),
        target_col=DEFAULT_TARGET_COL,
        date_col=DEFAULT_DATE_COL,
    )

    # 2. Test Forecast: conditioned strictly on train_df + val_df (first 155 rows)
    # Zero 2024 test data is seen by Chronos!
    history_for_test = pd.concat([train_df, val_df], ignore_index=True)
    test_fc = adapter.forecast(
        history_df=history_for_test[[DEFAULT_DATE_COL, DEFAULT_TARGET_COL]],
        horizon=len(test_df),
        target_col=DEFAULT_TARGET_COL,
        date_col=DEFAULT_DATE_COL,
    )

    # Align with actual target values
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
        "model": "Chronos-2",
        "split": "validation",
    })

    test_pred_rows = pd.DataFrame({
        "date": test_fc["date"].values,
        "actual": y_test_actual,
        "predicted": y_test_pred,
        "model": "Chronos-2",
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
