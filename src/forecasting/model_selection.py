"""
Model Evaluation and Selection Module for FreightWise Round 2 — Stage 2.2C.

Evaluates three forecasting candidates on identical chronological splits:
  - Naive Baseline (pred[t] = y[t-1], seeded with the final actual training target)
  - Round 1 XGBoost (existing final_xgboost_model.joblib, feature_names_in_ contract)
  - Round 2 LightGBM (existing lightgbm_freight_model.joblib, LIGHTGBM_FEATURES contract)

Model selection is based exclusively on validation MAE.
Tie-breakers: validation RMSE, then validation MAPE.
The 2024 test set is NEVER used for selection or tuning.

After selection, final performance is reported on the held-out 2024 test set.

Split contract (preserved exactly from Stage 2.1 / Stage 2.2A):
  Train:      143 observations  (2011-02-01 → 2022-12-01)
  Validation:  12 observations  (2023-01-01 → 2023-12-01)
  Test:        12 observations  (2024-01-01 → 2024-12-01)
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from .contracts import (
    DEFAULT_DATE_COL,
    DEFAULT_TARGET_COL,
    ForecastingDatasetContract,
    XGBOOST_26_FEATURES,
)
from .lightgbm_data import LIGHTGBM_FEATURES, prepare_lightgbm_datasets, LightGBMSplitResult
from .metrics import calculate_all_metrics

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
BENCHMARK_XGBOOST_MODEL_PATH: str = "ml/forecasting/final_xgboost_model.joblib"
LIGHTGBM_MODEL_PATH: str = "ml/forecasting/lightgbm_freight_model.joblib"
COMPARISON_CSV_PATH: str = "data/processed/forecasting_model_comparison.csv"

# Canonical candidate names — must be stable across all usages
CANDIDATE_NAIVE: str = "Naive Baseline"
CANDIDATE_XGBOOST: str = "Round 1 XGBoost"
CANDIDATE_LIGHTGBM: str = "Round 2 LightGBM"

SPLIT_VALIDATION: str = "validation"
SPLIT_TEST: str = "test"

# Selection metric keys (case-matches calculate_all_metrics output)
_PRIMARY_METRIC: str = "MAE"
_SECONDARY_METRIC: str = "RMSE"
_TERTIARY_METRIC: str = "MAPE"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class CandidateEvaluation:
    """
    Holds validation and test metrics for one forecast candidate.
    """

    name: str
    val_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    val_dates: List[str]
    test_dates: List[str]


@dataclass
class ModelSelectionResult:
    """
    Complete model selection result: per-candidate evaluations plus the
    deterministically selected winner (chosen on validation MAE alone).
    """

    candidates: List[CandidateEvaluation]
    selected_model: str
    selection_reason: str
    val_dates: List[str]
    test_dates: List[str]
    comparison_df: pd.DataFrame = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Naive baseline helper
# ---------------------------------------------------------------------------
def _naive_predictions(seed_value: float, y_true: pd.Series) -> np.ndarray:
    """
    Generates Naive (lag-1) predictions for a window.

    pred[0] = seed_value       (last actual observation from the preceding period)
    pred[t] = y_true[t-1]     (for t >= 1)

    This is exactly the Stage 2.2B Naive definition:
      val: seed = y_train.iloc[-1]
      test: seed = y_val.iloc[-1]

    Parameters
    ----------
    seed_value : float
        The last actual target value from the period immediately before this window.
    y_true : pd.Series
        Actual target values for this window (shape [n]).

    Returns
    -------
    np.ndarray of length n
    """
    values = y_true.tolist()
    return np.array([seed_value] + values[:-1], dtype=np.float64)


# ---------------------------------------------------------------------------
# XGBoost feature extraction helper
# ---------------------------------------------------------------------------
def _extract_xgboost_features(
    df_full: pd.DataFrame,
    dates: pd.Series,
    feature_names: List[str],
) -> pd.DataFrame:
    """
    Aligns rows in df_full to the requested date window and returns the
    exact ordered feature columns required by the XGBoost model.

    Parameters
    ----------
    df_full : pd.DataFrame
        Full freight_model_features DataFrame (167 rows).
    dates : pd.Series
        Date values identifying the desired rows.
    feature_names : List[str]
        model.feature_names_in_ — exact names and order expected by the model.

    Returns
    -------
    pd.DataFrame of shape (len(dates), len(feature_names))
    """
    date_set = set(pd.to_datetime(dates))
    mask = pd.to_datetime(df_full[DEFAULT_DATE_COL]).isin(date_set)
    subset = df_full[mask].copy().sort_values(DEFAULT_DATE_COL).reset_index(drop=True)

    missing = [f for f in feature_names if f not in subset.columns]
    if missing:
        raise KeyError(
            f"freight_model_features.csv is missing XGBoost feature(s): {missing}"
        )
    return subset[feature_names].copy()


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------
def evaluate_all_candidates(
    loader: Optional[Any] = None,
) -> ModelSelectionResult:
    """
    Evaluates Naive Baseline, Round 1 XGBoost, and Round 2 LightGBM
    on identical validation and test targets.

    Steps
    -----
    1. Prepare datasets using the existing Stage 2.2A split utility
       (143 train / 12 val / 12 test — reuses exact implementation, no new split).
    2. Generate validation and test predictions for each candidate:
       - Naive:    pred[t] = y[t-1], seeded with the last actual training value.
       - XGBoost:  load artifact → use model.feature_names_in_ →
                   align rows from freight_model_features.csv to val/test dates.
       - LightGBM: load artifact → use LIGHTGBM_FEATURES contract (43 features) →
                   use X_val / X_test already prepared by the split utility.
    3. Calculate MAE, RMSE, MAPE for each candidate × each split.
    4. Select winner purely on lowest validation MAE.
       Tie-breaker 1: validation RMSE (lower wins).
       Tie-breaker 2: validation MAPE (lower wins).
    5. NEVER use test metrics for selection.

    Parameters
    ----------
    loader : optional DataLoader instance.
        If None, creates a DataLoader internally.

    Returns
    -------
    ModelSelectionResult
    """
    # ------------------------------------------------------------------
    # 1. Load dataset and prepare the identical 143/12/12 split
    # ------------------------------------------------------------------
    if loader is None:
        from src.data.loader import DataLoader
        loader = DataLoader()

    df_full: pd.DataFrame = loader.load_freight_model_features()

    # Reuse existing Stage 2.2A split — no new logic, no shuffling
    split: LightGBMSplitResult = prepare_lightgbm_datasets(loader=loader)
    split.verify_no_leakage(target_col=DEFAULT_TARGET_COL)

    y_train: pd.Series = split.y_train.reset_index(drop=True)
    y_val: pd.Series   = split.y_val.reset_index(drop=True)
    y_test: pd.Series  = split.y_test.reset_index(drop=True)

    val_dates_list: List[str]  = [str(d) for d in split.val_dates.tolist()]
    test_dates_list: List[str] = [str(d) for d in split.test_dates.tolist()]

    # Guard: confirm partition sizes
    assert len(y_train) == 143, f"Expected 143 train rows, got {len(y_train)}"
    assert len(y_val)   == 12,  f"Expected 12 val rows, got {len(y_val)}"
    assert len(y_test)  == 12,  f"Expected 12 test rows, got {len(y_test)}"

    evaluations: List[CandidateEvaluation] = []

    # ==================================================================
    # 2a. Naive Baseline
    # ==================================================================
    # Validation: seed = last actual training target
    naive_val_seed: float = float(y_train.iloc[-1])
    naive_pred_val: np.ndarray = _naive_predictions(naive_val_seed, y_val)

    # Test: seed = last actual validation target  (Stage 2.2B definition)
    naive_test_seed: float = float(y_val.iloc[-1])
    naive_pred_test: np.ndarray = _naive_predictions(naive_test_seed, y_test)

    metrics_naive_val  = calculate_all_metrics(y_val,  naive_pred_val)
    metrics_naive_test = calculate_all_metrics(y_test, naive_pred_test)

    evaluations.append(CandidateEvaluation(
        name=CANDIDATE_NAIVE,
        val_metrics=metrics_naive_val,
        test_metrics=metrics_naive_test,
        val_dates=val_dates_list,
        test_dates=test_dates_list,
    ))

    # ==================================================================
    # 2b. Round 1 XGBoost
    # ==================================================================
    if not os.path.exists(BENCHMARK_XGBOOST_MODEL_PATH):
        raise FileNotFoundError(
            f"Round 1 XGBoost model not found at: {BENCHMARK_XGBOOST_MODEL_PATH}"
        )
    xgb_model = joblib.load(BENCHMARK_XGBOOST_MODEL_PATH)

    # Use model.feature_names_in_ for exact feature order (Requirement 7)
    if hasattr(xgb_model, "feature_names_in_"):
        xgb_feature_names: List[str] = [str(f) for f in xgb_model.feature_names_in_]
    else:
        xgb_feature_names = list(XGBOOST_26_FEATURES)

    X_val_xgb  = _extract_xgboost_features(df_full, split.val_dates,  xgb_feature_names)
    X_test_xgb = _extract_xgboost_features(df_full, split.test_dates, xgb_feature_names)

    xgb_pred_val  = xgb_model.predict(X_val_xgb)
    xgb_pred_test = xgb_model.predict(X_test_xgb)

    metrics_xgb_val  = calculate_all_metrics(y_val,  xgb_pred_val)
    metrics_xgb_test = calculate_all_metrics(y_test, xgb_pred_test)

    evaluations.append(CandidateEvaluation(
        name=CANDIDATE_XGBOOST,
        val_metrics=metrics_xgb_val,
        test_metrics=metrics_xgb_test,
        val_dates=val_dates_list,
        test_dates=test_dates_list,
    ))

    # ==================================================================
    # 2c. Round 2 LightGBM
    # ==================================================================
    if not os.path.exists(LIGHTGBM_MODEL_PATH):
        raise FileNotFoundError(
            f"Round 2 LightGBM model not found at: {LIGHTGBM_MODEL_PATH}"
        )
    lgb_model = joblib.load(LIGHTGBM_MODEL_PATH)

    # Use LIGHTGBM_FEATURES contract (43 features, exact order)
    assert len(LIGHTGBM_FEATURES) == 43, (
        f"LIGHTGBM_FEATURES contract must have 43 features, got {len(LIGHTGBM_FEATURES)}"
    )
    X_val_lgb  = split.X_val[LIGHTGBM_FEATURES].copy()
    X_test_lgb = split.X_test[LIGHTGBM_FEATURES].copy()

    lgb_pred_val  = lgb_model.predict(X_val_lgb)
    lgb_pred_test = lgb_model.predict(X_test_lgb)

    metrics_lgb_val  = calculate_all_metrics(y_val,  lgb_pred_val)
    metrics_lgb_test = calculate_all_metrics(y_test, lgb_pred_test)

    evaluations.append(CandidateEvaluation(
        name=CANDIDATE_LIGHTGBM,
        val_metrics=metrics_lgb_val,
        test_metrics=metrics_lgb_test,
        val_dates=val_dates_list,
        test_dates=test_dates_list,
    ))

    # ==================================================================
    # 3. Select winner — validation MAE only (test set never consulted)
    # ==================================================================
    # Sort deterministically: primary=val MAE (asc), secondary=val RMSE (asc),
    # tertiary=val MAPE (asc), then by name (asc) for perfect tie stability.
    ranked: List[CandidateEvaluation] = sorted(
        evaluations,
        key=lambda c: (
            round(c.val_metrics[_PRIMARY_METRIC],   6),
            round(c.val_metrics[_SECONDARY_METRIC], 6),
            round(c.val_metrics[_TERTIARY_METRIC],  6),
            c.name,
        ),
    )
    winner: CandidateEvaluation = ranked[0]

    # Build human-readable selection reason
    selection_reason: str = (
        f"Lowest validation {_PRIMARY_METRIC}: "
        f"{winner.val_metrics[_PRIMARY_METRIC]:.4f} "
        f"(RMSE={winner.val_metrics[_SECONDARY_METRIC]:.4f}, "
        f"MAPE={winner.val_metrics[_TERTIARY_METRIC]:.4f}%)"
    )

    # ==================================================================
    # 4. Build comparison DataFrame
    # ==================================================================
    rows: List[Dict] = []
    for cand in evaluations:
        is_selected_flag = (cand.name == winner.name)
        reason_text = selection_reason if is_selected_flag else ""

        rows.append({
            "model":            cand.name,
            "split":            SPLIT_VALIDATION,
            "mae":              round(cand.val_metrics["MAE"],  4),
            "rmse":             round(cand.val_metrics["RMSE"], 4),
            "mape":             round(cand.val_metrics["MAPE"], 4),
            "is_selected":      is_selected_flag,
            "selection_reason": reason_text,
        })
        rows.append({
            "model":            cand.name,
            "split":            SPLIT_TEST,
            "mae":              round(cand.test_metrics["MAE"],  4),
            "rmse":             round(cand.test_metrics["RMSE"], 4),
            "mape":             round(cand.test_metrics["MAPE"], 4),
            "is_selected":      False,     # test split never drives selection
            "selection_reason": "",
        })

    comparison_df = pd.DataFrame(rows, columns=[
        "model", "split", "mae", "rmse", "mape", "is_selected", "selection_reason"
    ])

    return ModelSelectionResult(
        candidates=evaluations,
        selected_model=winner.name,
        selection_reason=selection_reason,
        val_dates=val_dates_list,
        test_dates=test_dates_list,
        comparison_df=comparison_df,
    )


# ---------------------------------------------------------------------------
# CSV persistence
# ---------------------------------------------------------------------------
def save_comparison_csv(
    result: ModelSelectionResult,
    output_path: str = COMPARISON_CSV_PATH,
) -> str:
    """
    Saves the model comparison DataFrame to a CSV file.

    Schema columns: model, split, mae, rmse, mape, is_selected, selection_reason

    Parameters
    ----------
    result : ModelSelectionResult
    output_path : str

    Returns
    -------
    str — absolute path of the saved file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    result.comparison_df.to_csv(output_path, index=False)
    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------
def run_model_selection(
    loader: Optional[Any] = None,
    save_csv: bool = True,
    output_path: str = COMPARISON_CSV_PATH,
) -> ModelSelectionResult:
    """
    End-to-end model selection pipeline for Stage 2.2C.

    Evaluates all three candidates, selects the winner using validation MAE,
    optionally saves the comparison CSV, and returns the full result.

    Parameters
    ----------
    loader : optional DataLoader instance.
    save_csv : bool — whether to persist the comparison CSV (default True).
    output_path : str — output path for the comparison CSV.

    Returns
    -------
    ModelSelectionResult
    """
    result = evaluate_all_candidates(loader=loader)

    if save_csv:
        save_comparison_csv(result, output_path=output_path)

    return result
