# Stage 2.2C — Freight Forecasting Model Evaluation and Selection

**FreightWise Round 2 | ML Branch | Stage 2.2C**

---

## 1. Overview

Stage 2.2C implements a reproducible, validation-gated model-selection layer for the
FreightWise freight-rate forecasting pipeline. Three candidate models are evaluated on
identical chronological splits using common metrics. The winner is selected exclusively
on validation performance, and final results are reported on the held-out 2024 test set
only after selection is complete.

---

## 2. Model Candidates

| Candidate            | Source Artifact                                  | Features      |
|----------------------|--------------------------------------------------|---------------|
| **Naive Baseline**   | No artifact — rule-based (`pred[t] = y[t-1]`)   | None (lag-1)  |
| **Round 1 XGBoost**  | `ml/forecasting/final_xgboost_model.joblib`      | 26 (XGBOOST_26_FEATURES via `feature_names_in_`) |
| **Round 2 LightGBM** | `ml/forecasting/lightgbm_freight_model.joblib`   | 43 (LIGHTGBM_FEATURES) |

### Naive Baseline

The Naive baseline predicts that the next month's freight rate equals the current
month's actual freight rate (a lag-1 shift). This definition is preserved exactly
from Stage 2.2B:

```
pred[t] = y[t-1]
```

- **Validation seed**: `y_train.iloc[-1]` (last actual training observation, 2022-12-01).
- **Test seed**: `y_val.iloc[-1]` (last actual validation observation, 2023-12-01).
- No model predictions are used as input. No future actual values are used.

### Round 1 XGBoost

- Loads the existing `final_xgboost_model.joblib` — **read-only, never modified**.
- Feature column order and names are taken from `model.feature_names_in_` at runtime.
- Features are aligned from `freight_model_features.csv` by date-set intersection.

### Round 2 LightGBM

- Loads the existing `lightgbm_freight_model.joblib` — **read-only, never modified**.
- Feature matrix is derived from the Stage 2.2A `LightGBMDatasetPreparer` output.
- Exactly 43 features from `LIGHTGBM_FEATURES` contract, in declared order.

---

## 3. Chronological Split

The split is reused verbatim from Stage 2.1 / Stage 2.2A — no new split is created,
no shuffling, no modification.

| Partition     | Size | Date Range              |
|---------------|------|-------------------------|
| **Train**     | 143  | 2011-02-01 → 2022-12-01 |
| **Validation**| 12   | 2023-01-01 → 2023-12-01 |
| **Test**      | 12   | 2024-01-01 → 2024-12-01 |

**Total**: 167 observations (from `freight_model_features.csv`).

---

## 4. Metrics

Three metrics are calculated identically for all candidates on both validation and test
splits using `src/forecasting/metrics.py`:

| Metric | Formula |
|--------|---------|
| **MAE**  | mean(\|y_true − y_pred\|) |
| **RMSE** | √(mean((y_true − y_pred)²)) |
| **MAPE** | 100 × mean(\|y_true − y_pred\| / max(\|y_true\|, ε)) |

---

## 5. Validation-Based Model Selection

Model selection is performed **exclusively on validation metrics** (2023-01 → 2023-12).
The 2024 test set is completely isolated during selection.

### Selection Criteria

| Priority | Criterion           | Direction |
|----------|---------------------|-----------|
| 1 (primary)   | Validation MAE   | Lower wins |
| 2 (tie-break) | Validation RMSE  | Lower wins |
| 3 (tie-break) | Validation MAPE  | Lower wins |

The ranking is computed deterministically using `sorted()` with a tuple key, followed by
candidate name as a final stable tiebreaker.

### Why Test Metrics Are Not Used for Selection

Using test-set performance to pick a model inflates reported accuracy (a form of
implicit data snooping). The test set acts as an unbiased estimate of real-world
deployment performance — it must remain unseen until after the model is chosen.

---

## 6. Validation Results

| Candidate           | Val MAE   | Val RMSE  | Val MAPE  |
|---------------------|-----------|-----------|-----------|
| Naive Baseline      | 5,315.83  | 6,190.63  | 59.50%    |
| **Round 1 XGBoost** | **2,386.14** | **2,924.31** | **29.23%** |
| Round 2 LightGBM    | 3,181.95  | 4,512.26  | 36.84%    |

**Selected model: Round 1 XGBoost** — lowest validation MAE (2,386.14).

---

## 7. Final 2024 Test Set Performance

Reported on the held-out 2024 test set **after** model selection:

| Candidate           | Test MAE  | Test RMSE | Test MAPE |
|---------------------|-----------|-----------|-----------|
| Naive Baseline      | 2,802.67  | 4,153.06  | 42.45%    |
| **Round 1 XGBoost** | **2,117.82** | **3,111.19** | **36.75%** |
| Round 2 LightGBM    | 2,541.22  | 3,107.56  | 36.36%    |

The selected model (Round 1 XGBoost) achieves the best test MAE, confirming that
validation-based selection generalised correctly to the unseen 2024 period.

> **Note**: LightGBM achieves a marginally lower test RMSE and MAPE than XGBoost,
> but this was not visible during validation. The selection criterion (validation MAE)
> correctly identified the better-generalising model for the primary metric.

---

## 8. Output Artifacts

### `data/processed/forecasting_model_comparison.csv`

Six-row CSV (3 models × 2 splits) with schema:

```
model, split, mae, rmse, mape, is_selected, selection_reason
```

- `is_selected` is `True` only for the winning candidate's **validation** row.
- `selection_reason` is populated only for the winning row.
- Test split rows always have `is_selected=False` to preserve test-set isolation.

### Source: `src/forecasting/model_selection.py`

Key public API:

| Symbol | Description |
|--------|-------------|
| `run_model_selection()` | Top-level entry point — evaluates, selects, saves CSV. |
| `evaluate_all_candidates()` | Returns `ModelSelectionResult` without saving. |
| `save_comparison_csv()` | Persists `ModelSelectionResult.comparison_df` to CSV. |
| `ModelSelectionResult` | Dataclass: candidates, selected_model, comparison_df. |
| `COMPARISON_CSV_PATH` | Default output path constant. |

---

## 9. Test-Set Isolation Guarantees

The following mechanisms enforce strict test-set isolation:

1. **Split utility**: `chronological_train_val_test_split()` (Stage 2.1) enforces
   date disjointness via `verify_no_overlap()`.
2. **LightGBM training** (Stage 2.2B): test rows were never passed to `fit()` or
   early-stopping callbacks.
3. **Model selection** (Stage 2.2C): `is_selected` is set to `False` for all test rows
   in code, not as a post-hoc filter.
4. **Test suite**: `test_2c_test_set_not_used_for_selection()` explicitly asserts
   that no test row carries `is_selected=True`.

---

## 10. Reproducibility

| Mechanism | Implementation |
|-----------|---------------|
| Fixed random state | LightGBM: `random_state=42` (Stage 2.2B config) |
| Deterministic feature order | XGBoost: `feature_names_in_`; LightGBM: `LIGHTGBM_FEATURES` list |
| Stable sort | `sorted()` with tuple key including candidate name |
| No re-training | Both ML models are loaded from saved artifacts |
| Identical split | Stage 2.1 `chronological_train_val_test_split()` — no new split logic |

---

## 11. Limitations

- **Small test set**: 12 monthly observations limits the statistical power of the
  reported test metrics.
- **Naive overfitting on validation**: The Naive baseline performs worse on validation
  (MAE 5,315) than on test (MAE 2,802), suggesting the 2023 validation period had
  higher volatility. This makes validation-based selection appropriate: it captures
  the relative difficulty of the prediction task.
- **LightGBM underfitting**: LightGBM predictions from the saved model are nearly
  constant (early stopping converged quickly on 143 training examples with 43 features).
  With more data or cross-validation, LightGBM may perform better.
- **Target variable**: `bulk_carrier_handysize_usd_day` — a single freight-rate
  series. Generalisation to other vessel types or routes is not tested.

---

## 12. Why Chronos-2 and Prophet Are Deferred

| Model | Deferral Reason |
|-------|-----------------|
| **Chronos-2** | Requires substantial GPU inference infrastructure and a different prediction paradigm (zero-shot probabilistic). Integrating it within the current deterministic evaluation contract requires an additional adapter layer, proper quantile-to-point conversion, and GPU availability checks. Deferred to a dedicated stage. |
| **Prophet** | Prophet uses additive decomposition and requires a different date-indexing convention. Aligning its holiday/seasonality components with the existing feature contract and validating its predictions against identical y_val targets requires a separate integration stage. Additionally, Prophet's trend extrapolation assumptions may not suit the volatile, feature-rich freight environment without careful tuning. |

Neither model is excluded on performance grounds. Both are planned for evaluation in
a future stage when the infrastructure and evaluation contract can be extended cleanly
without violating the existing Stage 2.2A–2.2C contract boundaries.

---

## 13. File Index

| File | Role |
|------|------|
| `src/forecasting/model_selection.py` | Core evaluation and selection module |
| `data/processed/forecasting_model_comparison.csv` | Generated comparison output |
| `tests/test_model_selection_stage2_2c.py` | 12-test Stage 2.2C test suite |
| `docs/stage2_forecasting_model_selection.md` | This document |
| `src/forecasting/__init__.py` | Updated to expose Stage 2.2C API |
| `tests/run_tests.py` | Updated to include Stage 2.2C tests (46–57) |
