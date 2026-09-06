"""
Multi-Model Benchmark Comparison Module for FreightWise Round 2 — Stage 2.3.

Evaluates and compares all 5 forecasting models under the identical chronological split:
  1. Naive Baseline (lag-1 persistence seeded with last observed target)
  2. Round 1 XGBoost (feature_names_in_ contract, 26 features)
  3. Round 2 LightGBM (LIGHTGBM_FEATURES contract, 43 features)
  4. Prophet (univariate target-only, monthly)
  5. Chronos-2 (zero-shot foundation model, amazon/chronos-2, univariate)

Evaluation Contract:
  - Validation split: 2023-01-01 to 2023-12-01 (12 observations)
  - Test split:       2024-01-01 to 2024-12-01 (12 observations)
  - Identical target: bulk_carrier_handysize_usd_day
  - Metrics:          MAE, RMSE, MAPE (via calculate_all_metrics)

IMPORTANT:
  - Stage 2.2C selected Round 1 XGBoost based on validation MAE.
  - Stage 2.3 is an evaluation and benchmarking stage ONLY.
  - Does NOT automatically overwrite the Stage 2.2C production model selection.
  - Output is saved to data/processed/forecasting_stage2_3_comparison.csv.
  - data/processed/forecasting_model_comparison.csv is strictly PRESERVED.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from .chronos_forecast import CHRONOS_AVAILABLE, run_chronos_benchmark
from .contracts import DEFAULT_DATE_COL, DEFAULT_TARGET_COL
from .model_selection import (
    CANDIDATE_LIGHTGBM,
    CANDIDATE_NAIVE,
    CANDIDATE_XGBOOST,
    SPLIT_TEST,
    SPLIT_VALIDATION,
    evaluate_all_candidates,
)
from .prophet_forecast import PROPHET_AVAILABLE, run_prophet_benchmark

STAGE2_3_COMPARISON_CSV_PATH: str = "data/processed/forecasting_stage2_3_comparison.csv"

CANDIDATE_PROPHET: str = "Prophet"
CANDIDATE_CHRONOS2: str = "Chronos-2"

ALL_STAGE2_3_MODELS = [
    CANDIDATE_NAIVE,
    CANDIDATE_XGBOOST,
    CANDIDATE_LIGHTGBM,
    CANDIDATE_PROPHET,
    CANDIDATE_CHRONOS2,
]


@dataclass
class Stage2_3BenchmarkResult:
    """
    Container for Stage 2.3 multi-model evaluation comparison.
    """

    comparison_df: pd.DataFrame
    model_evaluations: Dict[str, Dict[str, Any]]
    selected_in_stage2_2c: str = CANDIDATE_XGBOOST


def run_stage2_3_benchmark(
    loader: Optional[Any] = None,
    save_csv: bool = True,
    output_path: str = STAGE2_3_COMPARISON_CSV_PATH,
    chronos_adapter: Optional[Any] = None,
    prophet_forecaster_cls: Optional[Any] = None,
) -> Stage2_3BenchmarkResult:
    """
    Runs the complete 5-model forecasting benchmark on identical validation and test splits.

    Parameters
    ----------
    loader : optional DataLoader instance.
    save_csv : bool
    output_path : str
    chronos_adapter : optional injected ChronosAdapter (for test efficiency/mocking).
    prophet_forecaster_cls : optional injected forecaster class.

    Returns
    -------
    Stage2_3BenchmarkResult
    """
    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()

    # 1. Obtain evaluations for Naive, XGBoost, LightGBM from Stage 2.2C
    stage2_2c_result = evaluate_all_candidates(loader=loader)
    evaluations_dict: Dict[str, Dict[str, Any]] = {}

    for cand in stage2_2c_result.candidates:
        evaluations_dict[cand.name] = {
            "val_metrics": cand.val_metrics,
            "test_metrics": cand.test_metrics,
            "val_dates": cand.val_dates,
            "test_dates": cand.test_dates,
        }

    # 2. Run Prophet benchmark
    if PROPHET_AVAILABLE or prophet_forecaster_cls is not None:
        kwargs = {"forecaster_cls": prophet_forecaster_cls} if prophet_forecaster_cls else {}
        prophet_res = run_prophet_benchmark(loader=loader, save_csv=save_csv, **kwargs)
        evaluations_dict[CANDIDATE_PROPHET] = {
            "val_metrics": prophet_res["val_metrics"],
            "test_metrics": prophet_res["test_metrics"],
            "val_dates": prophet_res["val_dates"],
            "test_dates": prophet_res["test_dates"],
        }
    else:
        evaluations_dict[CANDIDATE_PROPHET] = {
            "val_metrics": {"MAE": float("nan"), "RMSE": float("nan"), "MAPE": float("nan")},
            "test_metrics": {"MAE": float("nan"), "RMSE": float("nan"), "MAPE": float("nan")},
            "val_dates": stage2_2c_result.val_dates,
            "test_dates": stage2_2c_result.test_dates,
        }

    # 3. Run Chronos-2 benchmark
    if CHRONOS_AVAILABLE or chronos_adapter is not None:
        kwargs = {"adapter": chronos_adapter} if chronos_adapter else {}
        chronos_res = run_chronos_benchmark(loader=loader, save_csv=save_csv, **kwargs)
        evaluations_dict[CANDIDATE_CHRONOS2] = {
            "val_metrics": chronos_res["val_metrics"],
            "test_metrics": chronos_res["test_metrics"],
            "val_dates": chronos_res["val_dates"],
            "test_dates": chronos_res["test_dates"],
        }
    else:
        evaluations_dict[CANDIDATE_CHRONOS2] = {
            "val_metrics": {"MAE": float("nan"), "RMSE": float("nan"), "MAPE": float("nan")},
            "test_metrics": {"MAE": float("nan"), "RMSE": float("nan"), "MAPE": float("nan")},
            "val_dates": stage2_2c_result.val_dates,
            "test_dates": stage2_2c_result.test_dates,
        }

    # 4. Assemble comparison DataFrame
    # Models ordered logically: Naive, XGBoost, LightGBM, Prophet, Chronos-2
    notes_map = {
        CANDIDATE_NAIVE: "Lag-1 persistence baseline",
        CANDIDATE_XGBOOST: "Stage 2.2C Selected Model (26 domain features)",
        CANDIDATE_LIGHTGBM: "Stage 2.2B Candidate (43 domain features)",
        CANDIDATE_PROPHET: "Univariate additive model benchmark (no regressors)",
        CANDIDATE_CHRONOS2: "Zero-shot foundation model benchmark (amazon/chronos-2, univariate)",
    }

    rows: List[Dict[str, Any]] = []
    for model_name in ALL_STAGE2_3_MODELS:
        eval_data = evaluations_dict[model_name]
        is_selected = (model_name == CANDIDATE_XGBOOST)

        # Validation row
        rows.append({
            "model": model_name,
            "split": SPLIT_VALIDATION,
            "mae": round(eval_data["val_metrics"]["MAE"], 4),
            "rmse": round(eval_data["val_metrics"]["RMSE"], 4),
            "mape": round(eval_data["val_metrics"]["MAPE"], 4),
            "selected_in_stage2_2c": is_selected,
            "notes": notes_map[model_name],
        })

        # Test row
        rows.append({
            "model": model_name,
            "split": SPLIT_TEST,
            "mae": round(eval_data["test_metrics"]["MAE"], 4),
            "rmse": round(eval_data["test_metrics"]["RMSE"], 4),
            "mape": round(eval_data["test_metrics"]["MAPE"], 4),
            "selected_in_stage2_2c": is_selected,
            "notes": notes_map[model_name],
        })

    comparison_df = pd.DataFrame(rows, columns=[
        "model", "split", "mae", "rmse", "mape", "selected_in_stage2_2c", "notes"
    ])

    if save_csv:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        comparison_df.to_csv(output_path, index=False)

    return Stage2_3BenchmarkResult(
        comparison_df=comparison_df,
        model_evaluations=evaluations_dict,
        selected_in_stage2_2c=CANDIDATE_XGBOOST,
    )
