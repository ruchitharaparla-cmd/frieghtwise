# FreightWise Round 2 — Stage 2: Freight Forecasting Contract & Specification

This document defines the dataset contract, evaluation protocol, chronological train/validation/test splitting specification, and metrics framework for **FreightWise Stage 2: Freight Forecasting**.

---

## 1. Stage 2.1 Dataset Audit & Lineage

The Stage 2 forecasting framework builds directly upon the Stage 1 Data Foundation (`src.data.loader.DataLoader`), auditing three primary time-series datasets:

| Dataset Target | File Name | Rows | Columns | Date Range | Target / Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Freight Model Features** | `freight_model_features.csv` | 167 | 46 | 2011-02-01 to 2024-12-01 | Primary ML Feature Matrix; target `bulk_carrier_handysize_usd_day` |
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

The 46-column feature matrix in `freight_model_features.csv` includes macro-economic, vessel performance, port congestion, and lag features.

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
