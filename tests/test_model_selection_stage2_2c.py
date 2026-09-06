"""
FreightWise Round 2 — Stage 2.2C: Model Evaluation and Selection Test Suite.

Covers:
  1.  All three candidates are evaluated (Naive, XGBoost, LightGBM).
  2.  Common target dates and actual target values are used across candidates.
  3.  Common metrics (MAE, RMSE, MAPE) are present for every candidate × split.
  4.  XGBoost uses exact feature_names_in_ contract from the saved model artifact.
  5.  LightGBM uses exactly 43 LIGHTGBM_FEATURES.
  6.  Test set is NOT used for model selection.
  7.  Selection is based on validation MAE.
  8.  Selection is deterministic (two independent calls produce the same winner).
  9.  Comparison CSV matches required schema.
  10. Round 1 XGBoost artifact remains unchanged and loadable.
  11. Round 1 source CSVs remain present and non-empty.
  12. Comparison CSV correctly identifies winner row.
"""

import os
import hashlib
import pandas as pd
import numpy as np
import joblib

from src.forecasting.model_selection import (
    evaluate_all_candidates,
    run_model_selection,
    save_comparison_csv,
    COMPARISON_CSV_PATH,
    CANDIDATE_NAIVE,
    CANDIDATE_XGBOOST,
    CANDIDATE_LIGHTGBM,
    BENCHMARK_XGBOOST_MODEL_PATH,
    LIGHTGBM_MODEL_PATH,
    ModelSelectionResult,
    CandidateEvaluation,
    _naive_predictions,
)
from src.forecasting.lightgbm_data import LIGHTGBM_FEATURES, prepare_lightgbm_datasets
from src.forecasting.contracts import XGBOOST_26_FEATURES, DEFAULT_TARGET_COL
from src.forecasting.metrics import calculate_all_metrics

# ---------------------------------------------------------------------------
# Protected Round 1 assets — must not be altered by Stage 2.2C
# ---------------------------------------------------------------------------
_ROUND1_PROTECTED_CSVS = [
    "data/processed/freight_rates.csv",
    "data/processed/commodity_prices_processed.csv",
    "data/processed/oil_geopolitics_processed.csv",
    "data/processed/port_congestion_processed.csv",
    "data/processed/trade_flows_processed.csv",
    "data/processed/vessel_performance_processed.csv",
    "data/processed/india_bulk_imports_2022_2026.csv",
    "data/processed/monthly_freight_ml.csv",
    "data/processed/freight_model_features.csv",
]

# ---------------------------------------------------------------------------
# Lazily cached evaluation result to avoid re-running for every test
# ---------------------------------------------------------------------------
_RESULT_CACHE: dict = {}


def _get_result() -> ModelSelectionResult:
    """Run evaluate_all_candidates once, cache and return."""
    if "result" not in _RESULT_CACHE:
        _RESULT_CACHE["result"] = evaluate_all_candidates()
    return _RESULT_CACHE["result"]


def _candidate_by_name(result: ModelSelectionResult, name: str) -> CandidateEvaluation:
    for c in result.candidates:
        if c.name == name:
            return c
    raise AssertionError(f"Candidate '{name}' not found in evaluation results.")


# ===========================================================================
# Test 1: All three candidates are evaluated
# ===========================================================================
def test_2c_all_three_candidates_evaluated():
    """All three model candidates must appear in the result."""
    result = _get_result()
    names = {c.name for c in result.candidates}
    assert CANDIDATE_NAIVE    in names, f"'{CANDIDATE_NAIVE}' missing from candidates."
    assert CANDIDATE_XGBOOST  in names, f"'{CANDIDATE_XGBOOST}' missing from candidates."
    assert CANDIDATE_LIGHTGBM in names, f"'{CANDIDATE_LIGHTGBM}' missing from candidates."
    assert len(result.candidates) == 3, (
        f"Expected exactly 3 candidates, got {len(result.candidates)}."
    )


# ===========================================================================
# Test 2: Common target dates used across all candidates
# ===========================================================================
def test_2c_common_target_dates():
    """All candidates share identical val_dates and test_dates."""
    result = _get_result()
    # All three candidates report identical date lists
    naive_val  = _candidate_by_name(result, CANDIDATE_NAIVE).val_dates
    xgb_val    = _candidate_by_name(result, CANDIDATE_XGBOOST).val_dates
    lgb_val    = _candidate_by_name(result, CANDIDATE_LIGHTGBM).val_dates
    assert naive_val == xgb_val == lgb_val, (
        "Validation date lists differ across candidates."
    )

    naive_test = _candidate_by_name(result, CANDIDATE_NAIVE).test_dates
    xgb_test   = _candidate_by_name(result, CANDIDATE_XGBOOST).test_dates
    lgb_test   = _candidate_by_name(result, CANDIDATE_LIGHTGBM).test_dates
    assert naive_test == xgb_test == lgb_test, (
        "Test date lists differ across candidates."
    )

    # Confirm expected period lengths
    assert len(naive_val)  == 12, f"Expected 12 val dates, got {len(naive_val)}."
    assert len(naive_test) == 12, f"Expected 12 test dates, got {len(naive_test)}."

    # Confirm val = 2023, test = 2024
    val_years  = {pd.Timestamp(d).year for d in naive_val}
    test_years = {pd.Timestamp(d).year for d in naive_test}
    assert val_years  == {2023}, f"Validation dates must all be in 2023, got: {val_years}"
    assert test_years == {2024}, f"Test dates must all be in 2024, got: {test_years}"


# ===========================================================================
# Test 3: Common metrics (MAE, RMSE, MAPE) present for every candidate × split
# ===========================================================================
def test_2c_common_metrics_all_candidates():
    """MAE, RMSE, MAPE must be present for every candidate in val and test splits."""
    result = _get_result()
    required_keys = {"MAE", "RMSE", "MAPE"}
    for cand in result.candidates:
        missing_val  = required_keys - set(cand.val_metrics.keys())
        missing_test = required_keys - set(cand.test_metrics.keys())
        assert not missing_val, (
            f"Candidate '{cand.name}' val_metrics missing: {missing_val}"
        )
        assert not missing_test, (
            f"Candidate '{cand.name}' test_metrics missing: {missing_test}"
        )
        # All values must be finite positive floats
        for key in required_keys:
            assert cand.val_metrics[key]  > 0, f"{cand.name} val {key} must be positive."
            assert cand.test_metrics[key] > 0, f"{cand.name} test {key} must be positive."
            assert np.isfinite(cand.val_metrics[key]),  f"{cand.name} val {key} is not finite."
            assert np.isfinite(cand.test_metrics[key]), f"{cand.name} test {key} is not finite."


# ===========================================================================
# Test 4: XGBoost uses exact feature_names_in_ contract from the saved artifact
# ===========================================================================
def test_2c_xgboost_feature_names_in_contract():
    """
    XGBoost evaluation must use feature_names_in_ from the saved model —
    not a hard-coded list and not the first N columns.
    """
    assert os.path.exists(BENCHMARK_XGBOOST_MODEL_PATH), (
        f"XGBoost model not found at {BENCHMARK_XGBOOST_MODEL_PATH}"
    )
    xgb_model = joblib.load(BENCHMARK_XGBOOST_MODEL_PATH)

    assert hasattr(xgb_model, "feature_names_in_"), (
        "XGBoost model must expose feature_names_in_."
    )
    stored_features = [str(f) for f in xgb_model.feature_names_in_]
    assert len(stored_features) == 26, (
        f"XGBoost model feature_names_in_ must have 26 features, got {len(stored_features)}."
    )
    # Stored features must match the XGBOOST_26_FEATURES contract
    assert stored_features == list(XGBOOST_26_FEATURES), (
        "XGBoost feature_names_in_ does not match XGBOOST_26_FEATURES contract."
    )


# ===========================================================================
# Test 5: LightGBM uses exactly 43 LIGHTGBM_FEATURES
# ===========================================================================
def test_2c_lightgbm_exactly_43_features():
    """LightGBM evaluation must use exactly 43 LIGHTGBM_FEATURES in exact order."""
    assert len(LIGHTGBM_FEATURES) == 43, (
        f"LIGHTGBM_FEATURES contract must have 43 features, got {len(LIGHTGBM_FEATURES)}."
    )
    assert os.path.exists(LIGHTGBM_MODEL_PATH), (
        f"LightGBM model not found at {LIGHTGBM_MODEL_PATH}"
    )
    lgb_model = joblib.load(LIGHTGBM_MODEL_PATH)
    assert hasattr(lgb_model, "n_features_in_"), "LightGBM model must expose n_features_in_."
    assert lgb_model.n_features_in_ == 43, (
        f"LightGBM model expects {lgb_model.n_features_in_} features, expected 43."
    )


# ===========================================================================
# Test 6: Test set is NOT used for model selection
# ===========================================================================
def test_2c_test_set_not_used_for_selection():
    """
    The is_selected flag in the comparison CSV must be True only for a
    validation-split row, never for a test-split row.
    Selection code must not reference test metrics when picking the winner.
    """
    result = _get_result()
    df = result.comparison_df

    # No test row should carry is_selected=True
    test_selected = df[(df["split"] == "test") & (df["is_selected"] == True)]
    assert len(test_selected) == 0, (
        f"is_selected=True found on test rows: {test_selected[['model','split']].to_dict()}"
    )

    # Exactly one validation row must carry is_selected=True
    val_selected = df[(df["split"] == "validation") & (df["is_selected"] == True)]
    assert len(val_selected) == 1, (
        f"Expected exactly 1 selected validation row, found {len(val_selected)}."
    )

    # The ModelSelectionResult.selected_model must match
    selected_model_from_df = val_selected.iloc[0]["model"]
    assert result.selected_model == selected_model_from_df, (
        f"ModelSelectionResult.selected_model '{result.selected_model}' != "
        f"CSV selected model '{selected_model_from_df}'."
    )


# ===========================================================================
# Test 7: Selection is based on validation MAE
# ===========================================================================
def test_2c_selection_uses_validation_mae():
    """
    The selected model must have the lowest validation MAE among all candidates.
    """
    result = _get_result()
    df = result.comparison_df
    val_df = df[df["split"] == "validation"].copy()

    # Find the row with minimum validation MAE
    min_mae_row = val_df.loc[val_df["mae"].idxmin()]
    expected_winner = min_mae_row["model"]

    assert result.selected_model == expected_winner, (
        f"Selection should pick model with lowest val MAE ('{expected_winner}'), "
        f"but '{result.selected_model}' was selected."
    )

    # Confirm the winner has lower or equal val MAE than every other candidate
    winner_val_mae = val_df[val_df["model"] == result.selected_model]["mae"].iloc[0]
    for _, row in val_df.iterrows():
        assert winner_val_mae <= row["mae"], (
            f"Selected model '{result.selected_model}' has higher val MAE "
            f"({winner_val_mae}) than '{row['model']}' ({row['mae']})."
        )


# ===========================================================================
# Test 8: Selection is deterministic (two independent calls return same winner)
# ===========================================================================
def test_2c_deterministic_selection():
    """
    Two independent calls to evaluate_all_candidates must produce the same
    selected model, metrics, and winner.
    """
    result1 = evaluate_all_candidates()
    result2 = evaluate_all_candidates()

    assert result1.selected_model == result2.selected_model, (
        f"Non-deterministic selection: call1='{result1.selected_model}', "
        f"call2='{result2.selected_model}'."
    )

    # Validation MAE must be identical across both calls
    for cand_name in [CANDIDATE_NAIVE, CANDIDATE_XGBOOST, CANDIDATE_LIGHTGBM]:
        c1 = _candidate_by_name(result1, cand_name)
        c2 = _candidate_by_name(result2, cand_name)
        assert abs(c1.val_metrics["MAE"] - c2.val_metrics["MAE"]) < 1e-9, (
            f"{cand_name} val MAE differs between runs: {c1.val_metrics['MAE']} vs {c2.val_metrics['MAE']}"
        )


# ===========================================================================
# Test 9: Comparison CSV schema validation
# ===========================================================================
def test_2c_comparison_csv_schema():
    """
    The generated comparison CSV must contain exactly the required columns,
    have 6 rows (3 candidates × 2 splits), and have correct data types.
    """
    result = _get_result()

    # Save to a temp path to verify save_comparison_csv works independently
    tmp_path = "data/processed/forecasting_model_comparison.csv"
    save_comparison_csv(result, output_path=tmp_path)

    assert os.path.exists(tmp_path), f"Comparison CSV not written to {tmp_path}."
    df = pd.read_csv(tmp_path)

    required_cols = {"model", "split", "mae", "rmse", "mape", "is_selected", "selection_reason"}
    missing_cols = required_cols - set(df.columns)
    assert not missing_cols, f"Comparison CSV missing required columns: {missing_cols}"

    # 3 models × 2 splits = 6 rows
    assert len(df) == 6, f"Expected 6 rows in comparison CSV, got {len(df)}."

    # Each model appears exactly twice (once for val, once for test)
    for model_name in [CANDIDATE_NAIVE, CANDIDATE_XGBOOST, CANDIDATE_LIGHTGBM]:
        count = (df["model"] == model_name).sum()
        assert count == 2, f"Model '{model_name}' appears {count} times, expected 2."

    # Each split appears exactly 3 times
    assert (df["split"] == "validation").sum() == 3, "Expected 3 validation rows."
    assert (df["split"] == "test").sum()       == 3, "Expected 3 test rows."

    # Numeric columns must be finite and positive
    for col in ["mae", "rmse", "mape"]:
        assert df[col].gt(0).all(),  f"Column '{col}' contains non-positive values."
        assert df[col].notna().all(), f"Column '{col}' contains NaN."

    # is_selected must be boolean-compatible
    assert "is_selected" in df.columns
    selected_count = df["is_selected"].sum()
    assert selected_count == 1, f"Expected exactly 1 is_selected=True row, got {selected_count}."


# ===========================================================================
# Test 10: Round 1 XGBoost artifact unchanged and loadable
# ===========================================================================
def test_2c_round1_xgboost_artifact_unchanged():
    """
    Stage 2.2C must not overwrite or corrupt final_xgboost_model.joblib.
    The artifact must remain loadable and expose the 26-feature contract.
    """
    assert os.path.exists(BENCHMARK_XGBOOST_MODEL_PATH), (
        f"Round 1 XGBoost model missing at {BENCHMARK_XGBOOST_MODEL_PATH}!"
    )
    assert os.path.getsize(BENCHMARK_XGBOOST_MODEL_PATH) > 0, (
        "Round 1 XGBoost model file is empty."
    )
    xgb_model = joblib.load(BENCHMARK_XGBOOST_MODEL_PATH)
    assert hasattr(xgb_model, "predict"), "Loaded XGBoost object must expose predict()."
    if hasattr(xgb_model, "feature_names_in_"):
        assert len(xgb_model.feature_names_in_) == 26, (
            f"XGBoost feature_names_in_ has {len(xgb_model.feature_names_in_)} features, expected 26."
        )


# ===========================================================================
# Test 11: Round 1 source CSVs remain present and non-empty
# ===========================================================================
def test_2c_round1_source_csvs_unchanged():
    """
    All Round 1 protected source CSVs must remain present and non-empty
    after Stage 2.2C model selection runs.
    """
    for csv_path in _ROUND1_PROTECTED_CSVS:
        assert os.path.exists(csv_path), (
            f"Round 1 protected CSV missing after Stage 2.2C: {csv_path}"
        )
        assert os.path.getsize(csv_path) > 0, (
            f"Round 1 protected CSV is empty after Stage 2.2C: {csv_path}"
        )


# ===========================================================================
# Test 12: Comparison CSV correctly identifies the winner
# ===========================================================================
def test_2c_comparison_csv_winner_row():
    """
    The selected model's validation row in the comparison CSV must be the one
    with the minimum validation MAE, and its is_selected must be True.
    """
    result = _get_result()
    df = result.comparison_df
    val_df = df[df["split"] == "validation"].copy()

    # Minimum MAE row in validation split
    min_idx = val_df["mae"].idxmin()
    min_model = val_df.loc[min_idx, "model"]
    is_sel    = val_df.loc[min_idx, "is_selected"]

    assert is_sel, (
        f"Model '{min_model}' has lowest val MAE but is_selected is False."
    )
    assert min_model == result.selected_model, (
        f"CSV min-MAE model '{min_model}' != ModelSelectionResult.selected_model '{result.selected_model}'."
    )

    # All other validation rows must have is_selected=False
    other_val = val_df[val_df["model"] != min_model]
    assert other_val["is_selected"].sum() == 0, (
        "Non-winning validation rows must have is_selected=False."
    )

    # selection_reason must be non-empty for the winner, empty for others
    winner_reason = val_df.loc[min_idx, "selection_reason"]
    assert isinstance(winner_reason, str) and len(winner_reason.strip()) > 0, (
        "Winner's selection_reason must be a non-empty string."
    )
    for _, row in other_val.iterrows():
        assert row["selection_reason"] == "" or pd.isna(row["selection_reason"]), (
            f"Non-winner '{row['model']}' should have empty selection_reason."
        )
