# Round 2 Stage 2.4 — Freight Forecasting Production / Inference Layer

## Overview

The **Freight Forecasting Production / Inference Layer** provides a clean, stable, and reusable API wrapping the production-selected **Round 1 XGBoost** model (`ml/forecasting/final_xgboost_model.joblib`).

Downstream FreightWise modules—such as risk calculation, port delay/congestion impact, fleet optimization, bunker procurement, and dashboard analytics—consume freight rate forecasts through this unified service layer without needing to manage model serialization, feature engineering pipelines, or train/test splits.

---

## Architectural Principles

1. **Immutable Production Artifact**:
   The service uses the frozen XGBoost model selected in Stage 2.2C (lowest validation MAE: 2,386.14 USD/day). The model is never retrained or modified on instantiation or inference.
2. **Zero-Imputation Strict Contract**:
   The model requires exactly 26 numeric features derived from macro, commodity, freight lag, and seasonal indices. If any required feature is absent or contains `null`/`NaN`, inference fails immediately with an explicit, informative `ValueError`. Arbitrary or silent imputation is strictly prohibited.
3. **Robust Input Reordering**:
   Input DataFrames are allowed to contain extra metadata, target columns, or extraneous features. The service isolates and orders the exact 26 features according to `model.feature_names_in_`, guaranteeing feature alignment even if inputs are passed with shuffled columns.
4. **Independent Date Tracking**:
   The forecast `date` is mandatory for tracking and timeline alignment, but is kept completely separate from feature inputs and is never passed into the XGBoost model. Output predictions maintain strict row-by-row correspondence with the input dates.
5. **Artifact Integrity Guard**:
   The model artifact's SHA-256 hash (`07820057afecbe0010dcc9fcf3bd7559d435bdfafee2336afa268bd1a3e41396`) is verified on load as a regression guard against unintentional modifications or artifact corruption.

---

## Service API

### Class: `FreightForecastService`

```python
from src.forecasting import FreightForecastService

# 1. Instantiate the service (loads model once, cached in-memory)
service = FreightForecastService()
```

#### Initialization Arguments
- `model_path` *(Optional[str])*: Path to the model artifact. Defaults to `"ml/forecasting/final_xgboost_model.joblib"`.
- `auto_load` *(bool)*: If `True` (default), loads model upon initialization.
- `verify_checksum` *(bool)*: If `True` (default), validates the SHA-256 checksum against `EXPECTED_XGBOOST_SHA256`.

---

### Single Prediction: `service.predict()`

Accepts a single observation as a `dict`, `pd.Series`, or 1-row `pd.DataFrame`.

```python
sample_input = {
    "date": "2025-01-01",
    "freight_lag_1": 13500.0,
    "freight_lag_3": 13200.0,
    "freight_lag_6": 12800.0,
    "freight_lag_12": 11500.0,
    "freight_rolling_mean_3": 13350.0,
    "freight_rolling_mean_6": 13100.0,
    "freight_rolling_mean_12": 12400.0,
    "freight_rolling_std_3": 180.0,
    "baltic_dry_index_lag_1": 1450.0,
    "baltic_dry_index_lag_3": 1400.0,
    "brent_price_lag_1": 78.5,
    "brent_price_lag_3": 81.2,
    "wti_price_lag_1": 74.1,
    "wti_price_lag_3": 76.8,
    "dxy_index_lag_1": 103.2,
    "dxy_index_lag_3": 104.0,
    "vix_lag_1": 14.5,
    "vix_lag_3": 15.2,
    "gpr_index_lag_1": 110.0,
    "gpr_index_lag_3": 105.0,
    "thermal_coal_price_lag_1": 132.0,
    "thermal_coal_price_lag_3": 135.0,
    "month_num": 1,
    "quarter": 1,
    "month_sin": 0.5,
    "month_cos": 0.866025,
}

result = service.predict(sample_input)
```

#### Output Schema:
```python
{
    "model_name": "Round 1 XGBoost",
    "model_version": "07820057afecbe0010dcc9fcf3bd7559d435bdfafee2336afa268bd1a3e41396",
    "forecast_date": "2025-01-01",
    "predicted_freight_rate": 13421.50,
    "unit": "USD/day"
}
```

---

### Batch Prediction: `service.predict_batch()`

Accepts a `pd.DataFrame` containing multiple rows.

```python
import pandas as pd
from src.data.loader import DataLoader
from src.forecasting import FreightForecastService

loader = DataLoader()
df_features = loader.load_freight_model_features()

service = FreightForecastService()
forecasts_df = service.predict_batch(df_features)

print(forecasts_df.head())
```

#### Output DataFrame Schema:
| Column | Type | Description |
|---|---|---|
| `forecast_date` | `str` | ISO formatted date string (`YYYY-MM-DD`) matching the input |
| `predicted_freight_rate` | `float` | Model point forecast in USD/day |
| `model_name` | `str` | `"Round 1 XGBoost"` |
| `model_version` | `str` | SHA-256 hash of the model artifact |
| `unit` | `str` | `"USD/day"` |

---

## Required Features (26 Contract)

The 26 features defined in `XGBOOST_26_FEATURES` and `model.feature_names_in_`:

| Category | Feature Name | Description |
|---|---|---|
| **Freight Lags** | `freight_lag_1`, `freight_lag_3`, `freight_lag_6`, `freight_lag_12` | Historical freight rates at 1, 3, 6, 12 months lag |
| **Freight Rolling** | `freight_rolling_mean_3`, `freight_rolling_mean_6`, `freight_rolling_mean_12`, `freight_rolling_std_3` | Rolling means & volatility over 3, 6, 12 months |
| **Baltic Dry Index** | `baltic_dry_index_lag_1`, `baltic_dry_index_lag_3` | Shipping market index lags |
| **Crude Oil** | `brent_price_lag_1`, `brent_price_lag_3`, `wti_price_lag_1`, `wti_price_lag_3` | Global energy price indicators |
| **Currency & Volatility**| `dxy_index_lag_1`, `dxy_index_lag_3`, `vix_lag_1`, `vix_lag_3` | US Dollar index and equity market fear gauge |
| **Geopolitical & Coal** | `gpr_index_lag_1`, `gpr_index_lag_3`, `thermal_coal_price_lag_1`, `thermal_coal_price_lag_3` | Geopolitical risk and dry bulk commodity price |
| **Calendar / Seasonality**| `month_num`, `quarter`, `month_sin`, `month_cos` | Month, quarter, and harmonic trigonometric seasonal terms |

---

## How Downstream Modules Should Call the Inference Layer

- **Risk & Sensitivity Module**:
  Query `service.predict()` or `service.predict_batch()` under varying macroeconomic and fuel lag conditions to compute freight rate downside bounds and Value-at-Risk (VaR).
- **Optimization & Procurement Modules**:
  Feed forward-looking monthly rate forecasts from `service.predict_batch()` into the chartering optimizer (spot vs time charter allocation).
- **Executive Dashboard**:
  Retrieve forecasts along with `model_name`, `model_version`, and `unit` directly from `predict_batch()` for display in trend charts and rate comparison tables.
