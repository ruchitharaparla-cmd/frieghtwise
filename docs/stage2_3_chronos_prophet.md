# FreightWise Round 2 — Stage 2.3: Chronos-2 and Prophet Forecasting Benchmarks

## Executive Summary

Stage 2.3 integrates **Chronos-2** (pretrained `amazon/chronos-2` foundation model) and **Prophet** (univariate generalized additive model) as standardized forecasting benchmarks alongside the existing Stage 2.2C candidates (Naive Baseline, Round 1 XGBoost, and Round 2 LightGBM).

> [!IMPORTANT]
> **Benchmarking Scope & Model Selection Continuity**:
> Stage 2.3 is an evaluation and benchmarking milestone only. In accordance with strict governance rules, **Stage 2.3 does not automatically replace or overwrite the selected production model from Stage 2.2C (Round 1 XGBoost)**. Round 1 XGBoost remains the selected forecasting model for downstream consumption.

---

## Benchmark Motivation

1. **Why Chronos-2?**
   - Chronos-2 is a modern, pretrained probabilistic time-series foundation model developed by Amazon. It uses a transformer-based architecture trained on billions of time-series observations across diverse domains.
   - Adding Chronos-2 tests whether zero-shot foundation models can forecast volatile dry bulk freight rates without domain-specific feature engineering or local fine-tuning.

2. **Why Prophet?**
   - Prophet is an established, interpretable additive time-series forecasting model developed by Meta, widely used across industry for capturing trend changes and multi-scale seasonality.
   - Benchmarking Prophet provides a univariate statistical baseline to compare against feature-driven gradient boosting algorithms (XGBoost, LightGBM) and deep neural foundation models (Chronos-2).

---

## Methodology & Model Architectures

### 1. Chronos-2 Zero-Shot Architecture
- **Pretrained Weights**: `amazon/chronos-2` (Hugging Face Hub / local cache).
- **Execution Mode**: Strictly **zero-shot inference** — no parameter updating, no adapter fine-tuning, no transfer retraining.
- **Univariate Configuration**: Conditioned exclusively on the historical target series (`bulk_carrier_handysize_usd_day`). No external covariates, sentiment signals, or vessel performance metrics were passed.
- **Decoupled Adapter**: Wrapped in `ChronosAdapter` in `src/forecasting/chronos_forecast.py` to prevent tight coupling of FreightWise components to Chronos internals, featuring an in-memory singleton pipeline cache to eliminate redundant model loading.
- **Point Forecast Selection**: The median (0.50 quantile) forecast was extracted to provide robust point predictions aligned with monthly timestamps (`freq='MS'`).

### 2. Prophet Univariate Benchmark
- **Model Framework**: Prophet (via `cmdstanpy` backend).
- **Input Contract**: Standard `ds` (date) and `y` (`bulk_carrier_handysize_usd_day`) columns.
- **Seasonality & Trend**: Automatic changepoint detection with yearly seasonality enabled for monthly observations; no external regressors.
- **Horizon**: 12-month recursive/direct forecasting.

---

## Chronological Split & Test-Set Isolation

All five models are evaluated against the exact, verified chronological partition established in Stage 2.1 / Stage 2.2A:

| Partition | Observation Count | Date Range (Inclusive) | Role in Evaluation |
| :--- | :---: | :---: | :--- |
| **Train** | 143 | `2011-02-01` → `2022-12-01` | Model fitting / zero-shot conditioning |
| **Validation** | 12 | `2023-01-01` → `2023-12-01` | Candidate evaluation & benchmark comparison |
| **Test** | 12 | `2024-01-01` → `2024-12-01` | Final out-of-sample evaluation |
| **Total** | **167** | `2011-02-01` → `2024-12-01` | Fully accounted for, zero shuffle |

### Strict No-Leakage Verification
- **Validation Forecast (2023)**: Conditioned / fitted strictly on the first 143 observations (`2011-02-01` through `2022-12-01`).
- **Test Forecast (2024)**: Conditioned / fitted strictly on the first 155 observations (`2011-02-01` through `2023-12-01`).
- **2024 Isolation**: Zero 2024 test observations were passed to model fitting, hyperparameter selection, prompt conditioning, or tuning before final evaluation.

---

## Benchmark Results (5-Model Comparison)

Evaluation metrics were computed using the analytical functions in `src/forecasting/metrics.py` (`MAE`, `RMSE`, `MAPE` in USD/day and percentage):

| Model | Split | MAE (USD/day) | RMSE (USD/day) | MAPE (%) | Selected in Stage 2.2C | Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Naive Baseline** | Validation (2023) | 5315.83 | 6190.63 | 59.50% | No | Lag-1 persistence baseline |
| **Naive Baseline** | Test (2024) | 2802.67 | 4153.06 | 42.45% | No | Lag-1 persistence baseline |
| **Round 1 XGBoost** | **Validation (2023)** | **2386.14** | **2924.31** | **29.23%** | **Yes** | **Stage 2.2C Selected Model (26 domain features)** |
| **Round 1 XGBoost** | **Test (2024)** | **2117.82** | **3111.19** | **36.75%** | **Yes** | **Stage 2.2C Selected Model (26 domain features)** |
| **Round 2 LightGBM** | Validation (2023) | 3181.95 | 4512.26 | 36.84% | No | Stage 2.2B Candidate (43 domain features) |
| **Round 2 LightGBM** | Test (2024) | 2541.22 | 3107.56 | 36.36% | No | Stage 2.2B Candidate (43 domain features) |
| **Prophet** | Validation (2023) | 3790.83 | 5113.81 | 41.86% | No | Univariate additive model benchmark (no regressors) |
| **Prophet** | Test (2024) | 2606.61 | 3406.32 | 35.36% | No | Univariate additive model benchmark (no regressors) |
| **Chronos-2** | Validation (2023) | 3681.64 | 4910.41 | 39.62% | No | Zero-shot foundation model benchmark (amazon/chronos-2) |
| **Chronos-2** | Test (2024) | 2232.92 | 3032.76 | 35.42% | No | Zero-shot foundation model benchmark (amazon/chronos-2) |

---

## Detailed Performance Analysis

### 1. Validation Performance (Model Selection Criteria)
- **Round 1 XGBoost** maintains the best validation MAE (**2386.14 USD/day**), significantly outperforming all other candidates.
- **Chronos-2** (zero-shot) achieves a validation MAE of **3681.64 USD/day**, outperforming Prophet (3790.83 USD/day) and Naive (5315.83 USD/day), but trailing XGBoost and LightGBM.
- **Prophet** performs adequately (3790.83 USD/day) but struggles to capture post-pandemic macroeconomic rate deflation without external regressors.

### 2. Held-Out 2024 Test Performance
- **Round 1 XGBoost** achieves the lowest test MAE (**2117.82 USD/day**).
- **Chronos-2** demonstrates impressive zero-shot generalization on the 2024 test horizon, achieving **2232.92 USD/day MAE** and the lowest RMSE overall (**3032.76 USD/day**), narrowly trailing XGBoost in MAE without ever having seen any domain features or undergoing fine-tuning.
- **LightGBM** achieves **2541.22 USD/day**, and **Prophet** achieves **2606.61 USD/day**.

### 3. Key Takeaways
1. **Domain Features vs. Zero-Shot Foundation Models**:
   - Round 1 XGBoost's 26 curated domain features (bunker fuel prices, iron ore/coal imports, port congestion, fleet capacity) provide decisive predictive power during turbulent validation periods (2023).
   - However, Chronos-2 demonstrates that pre-trained foundational time-series representations capture secular trends and mean reversion remarkably well zero-shot.
2. **Model Selection Integrity**:
   - Because model selection was finalized in Stage 2.2C based strictly on validation MAE, **Round 1 XGBoost remains the selected model**.
   - Chronos-2 serves as an outstanding candidate for future hybrid or ensemble experiments (e.g., in Stage 3).

---

## Limitations

1. **Univariate Isolation**:
   - Neither Chronos-2 nor Prophet utilized exogenous covariates in this benchmark. Adding commodity prices and vessel metrics as covariates or regressors may further improve their accuracy.
2. **Zero-Shot Foundation Constraints**:
   - Chronos-2 was evaluated without fine-tuning. Downstream task-specific fine-tuning on maritime shipping indices could adapt the transformer embeddings to maritime volatility.
3. **Monthly Granularity**:
   - 143 historical training observations is relatively small for deep transformer foundation models, although Chronos-2 compensates via pretraining on large-scale cross-domain corpora.

---

## Dependency Requirements

- `chronos-forecasting` >= 2.3.1 (with `torch` >= 2.2, CPU or CUDA, `transformers` >= 4.41, `accelerate` >= 1.1.0)
- `prophet` >= 1.4.0 (with `cmdstanpy` >= 1.0.4)
- `pandas` >= 2.0
- `scikit-learn` >= 1.3
- Pretrained weights for `amazon/chronos-2` cached in `~/.cache/huggingface/hub/models--amazon--chronos-2`.

---

## Generated Artifacts

- `src/forecasting/chronos_forecast.py` — Chronos-2 decoupled adapter & benchmark runner
- `src/forecasting/prophet_forecast.py` — Univariate Prophet forecaster & benchmark runner
- `src/forecasting/benchmark_stage2_3.py` — 5-model unified evaluation runner
- `data/processed/chronos2_forecast_predictions.csv` — Chronos-2 validation and test predictions
- `data/processed/prophet_forecast_predictions.csv` — Prophet validation and test predictions
- `data/processed/forecasting_stage2_3_comparison.csv` — Complete 5-model × 2-split comparison table
- `tests/test_forecasting_stage2_3.py` — 17 unit and contract validation tests
