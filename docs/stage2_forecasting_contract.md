# FreightWise Round 2 — Stage 2: Freight Forecasting Contract & Specification

This document defines the dataset contract, evaluation protocol, chronological train/validation/test splitting specification, metrics framework, and LightGBM foundation contract for **FreightWise Stage 2: Freight Forecasting**.

---

## 1. Stage 2.1 Dataset Audit & Lineage

The Stage 2 forecasting framework builds directly upon the Stage 1 Data Foundation (`src.data.loader.DataLoader`), auditing three primary time-series datasets:

| Dataset Target | File Name | Rows | Columns | Date Range | Target / Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Freight Model Features** | `freight_model_features.csv` | 167 | 47 | 2011-02-01 to 2024-12-01 | Primary ML Feature Matrix; target `bulk_carrier_handysize_usd_day` |
| **Monthly Freight ML** | `monthly_freight_ml.csv` | 179 | 21 | 2010-02-01 to 2024-12-01 | Merged Monthly Base Data; Target `bulk_carrier_handysize_usd_day` |
| **Freight Rates Base** | `freight_rates.csv` | 300 | 12 | 2000-01-01 to 2024-12-01 | Raw Historical Shipping Rates |

### Data Foundation Principles:
- **No Missing Data Invention**: Imputation or synthetic generation of missing observations is strictly prohibited.
- **Copy Immutability**: All loaders and split functions return explicit DataFrame copies, guaranteeing original source files remain pristine.

---

## 2. Chronological Train / Validation / Test Splitting Contract

To evaluate time-series forecasting models without temporal data leakage or lookahead bias, we preserve the **Round 1 Chronological Split Philosophy**:

$$N_{\text{total}} = 167 \implies N_{\text{train}} = 143, \quad N_{\text{val}} = 12, \quad N_{\text{test}} = 12$$

### Split Partition Boundaries:
1. **Training Partition** (143 observations): `2011-02-01` to `2022-12-01`
2. **Validation Partition** (12 observations): `2023-01-01` to `2023-12-01` (Calendar Year 2023)
3. **Test Partition** (12 observations): `2024-01-01` to `2024-12-01` (Calendar Year 2024)

### Zero Leakage & Ordering Rules:
- **Chronological Sorting**: Datasets are sorted strictly by date prior to partitioning. Random shuffling is strictly prohibited.
- **Strict Boundary Separation**:
  $$\max(\text{train\_date}) < \min(\text{val\_date}) < \min(\text{test\_date})$$
- **Disjoint Indices**: The index sets of train, validation, and test partitions are completely disjoint ($\text{train} \cap \text{val} = \emptyset$, $\text{val} \cap \text{test} = \emptyset$, $\text{train} \cap \text{test} = \emptyset$).

---

## 3. Standard Evaluation Metrics

Model evaluation across validation and test sets is governed by a unified metrics module (`src.forecasting.metrics`) returning three core error metrics:

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
3. **Mean Absolute Percentage Error (MAPE %)**:
   $$\text{MAPE} = \frac{100}{n} \sum_{i=1}^n \left| \frac{y_i - \hat{y}_i}{\max(|y_i|, \epsilon)} \right|$$

Evaluation outputs adhere to `EvaluationResultContract`, standardizing output metrics for comparison across baseline and future forecasting models.

---

## 4. XGBoost 26-Feature Contract Separation

The 47-column feature dataset in `freight_model_features.csv` includes macro-economic, vessel performance, port congestion, and lag features.

However, the existing saved Round 1 XGBoost model (`ml/forecasting/final_xgboost_model.joblib`) expects an **exact 26-feature input contract** matching `ml/forecasting/model_features.csv`:

```
freight_lag_1, freight_lag_3, freight_lag_6, freight_lag_12,
freight_rolling_mean_3, freight_rolling_mean_6, freight_rolling_mean_12, freight_rolling_std_3,
baltic_dry_index_lag_1, baltic_dry_index_lag_3, brent_price_lag_1, brent_price_lag_3,
wti_price_lag_1, wti_price_lag_3, dxy_index_lag_1, dxy_index_lag_3,
vix_lag_1, vix_lag_3, gpr_index_lag_1, gpr_index_lag_3,
thermal_coal_price_lag_1, thermal_coal_price_lag_3,
month_num, quarter, month_sin, month_cos
```

`ForecastingDatasetContract.extract_xgboost_features()` isolates and orders these 26 features dynamically, keeping the XGBoost contract separate from the broader feature dataset.

---

## 5. LightGBM Freight Forecasting Foundation (Stage 2.2A)

### 5.1 Role of LightGBM in FreightWise Round 2
LightGBM is introduced in Round 2 to evaluate gradient boosted decision trees on the broader freight feature set (43 numeric features), serving as an advanced benchmark alongside the Round 1 XGBoost 26-feature model.

> [!NOTE]
> Stage 2.2A establishes the **data preparation and model configuration contract ONLY**. LightGBM model training, fitting, evaluation, hyperparameter tuning, and model comparison are intentionally excluded from Stage 2.2A and reserved for future stages.

### 5.2 Source Dataset & Feature Derivation
LightGBM dataset preparation operates via `src.forecasting.lightgbm_data.LightGBMDatasetPreparer`.

The approved feature contract `LIGHTGBM_FEATURES` is derived dynamically by inspecting `freight_model_features.csv` and excluding:
1. **Metadata Date Columns**: `date`, `year_month`, `canonical_month_start`.
2. **Target Column**: `bulk_carrier_handysize_usd_day`.
3. **Non-numeric / Identifier Fields**: Any non-numeric columns.
4. **Leaking Features**: Features failing temporal leakage checks.

#### Actual Feature Count: **43 Numeric Features**

#### Approved LightGBM Feature List (`LIGHTGBM_FEATURES`):
```
baltic_dry_index, tanker_rate_aframax_usd_day, supply_chain_pressure_index, on_time_delivery_pct,
bdi_mom_change_pct, container_yoy_pct, brent_price, wti_price, dxy_index, vix, gpr_index,
brent_volatility_30d, wti_volatility_30d, brent_wti_spread, event_severity, event_flag,
thermal_coal_price, freight_lag_1, freight_lag_3, freight_lag_6, freight_lag_12,
freight_rolling_mean_3, freight_rolling_mean_6, freight_rolling_mean_12, freight_rolling_std_3,
month_num, quarter, month_sin, month_cos, baltic_dry_index_lag_1, baltic_dry_index_lag_3,
brent_price_lag_1, brent_price_lag_3, wti_price_lag_1, wti_price_lag_3, dxy_index_lag_1,
dxy_index_lag_3, vix_lag_1, vix_lag_3, gpr_index_lag_1, gpr_index_lag_3,
thermal_coal_price_lag_1, thermal_coal_price_lag_3
```

### 5.3 Temporal Leakage Audit
Every candidate feature was audited for temporal leakage:
- **Lag Features** (`freight_lag_1`, `baltic_dry_index_lag_1`, etc.): Use strictly past observations ($t-1, t-3, \dots$).
- **Rolling Statistics** (`freight_rolling_mean_3`, `freight_rolling_std_3`): Computed over prior observations before timestamp $t$. Target $y_t$ is strictly excluded.
- **Zero Future Lookahead**: No future-derived or future-shifted target variables exist.
- **Preprocessing Leakage Protection**: Feature splitting occurs chronologically *before* any preprocessing. Scalers or imputers are never fit on validation or test partitions during training.

### 5.4 Chronological Split Alignment
Reuses the Stage 2.1 chronological split philosophy:
- **Train (143 observations)**: `2011-02-01` to `2022-12-01` ($X_{\text{train}}: 143 \times 43$, $y_{\text{train}}: 143$)
- **Validation (12 observations)**: `2023-01-01` to `2023-12-01` ($X_{\text{val}}: 12 \times 43$, $y_{\text{val}}: 12$)
- **Test (12 observations)**: `2024-01-01` to `2024-12-01` ($X_{\text{test}}: 12 \times 43$, $y_{\text{test}}: 12$)

### 5.5 Model Configuration Contract (`LightGBMModelConfig`)
LightGBM hyperparameter configuration is specified in `src/forecasting/lightgbm_config.py`:
- `objective`: `"regression"`
- `metric`: `"rmse"`
- `learning_rate`: `0.05`
- `n_estimators`: `100`
- `num_leaves`: `31`
- `max_depth`: `-1`
- `min_child_samples`: `20`
- `subsample`: `0.8`
- `colsample_bytree`: `0.8`
- `random_state`: `42`
- `verbose`: `-1`
