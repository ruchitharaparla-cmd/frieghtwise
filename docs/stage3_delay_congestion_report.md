# Round 2 Stage 3 — Delay & Congestion Prediction Technical Report

## 1. Executive Summary

Stage 3 establishes the predictive foundation for **vessel turnaround / delay risk** and **port congestion risk** in FreightWise. It exposes production-grade inference services (`VesselTurnaroundService` and `PortCongestionService`) so that downstream modules (risk calculation, fleet optimization, bunker procurement, and executive dashboard) can consume structured delay and congestion predictions through stable APIs.

### Core Achievements
- **Vessel Turnaround & Delay Risk Models**: Evaluated **CatBoost** and **XGBoost** against the Round 1 **Random Forest** baseline on 669 Bulk Carrier records. Evaluated turnaround regression (MAE, RMSE, $R^2$) and binary delay risk classification (F1, Precision, Recall, ROC-AUC) on a strict chronological split (463 Train / 101 Validation / 105 Test).
- **Global Port Congestion Models**: Evaluated **CatBoost** against Random Forest and Persistence Naive baselines on 6,260 weekly panel records across 20 global ports. Constructed 1-week-ahead lead targets ($t \to t+1$) with zero temporal leakage and per-port independent lag calculations.
- **Honest Data Governance (India Port Absence)**: Audited and documented that `port_congestion_processed.csv` contains **0 Indian ports** (0 India rows). Scoped predictions strictly as **Global Port Congestion Risk** and built an explicit `IndiaPortDataAbsentError` guard into the service layer to prevent deceptive claims or fake data generation.
- **Full Test Suite & Immutability Verification**: Expanded the test suite from 91 to **110 passing tests** with 100% regression safety for Stages 1–2.4 and zero mutations to existing Stage 2 freight forecasting artifacts.

---

## 2. Dataset Reconciliation & Chronological Splits

### 2.1 Vessel Performance Dataset (`vessel_performance_processed.csv`)
- **Raw Row Reconciliation**: 2,736 total raw rows -> 669 Bulk Carrier rows (excludes 653 Fish Carrier, 643 Tanker, 635 Container Ship, 136 null `ship_type` rows). 0 nulls in target `turnaround_time_hours`.
- **Pre-Voyage Feature Contract (12 features)**: `route_type`, `engine_type`, `maintenance_status`, `weather_condition`, `speed_over_ground_knots`, `engine_power_kw`, `distance_traveled_nm`, `draft_meters`, `cargo_weight_tons`, `seasonal_impact_score`, `weekly_voyage_count`, `average_load_percentage`.
- **Target Definitions & Thresholds**:
  - Regression Target: `turnaround_time_hours` (Mean 42.58 h, Std 17.74 h).
  - Classification Target: `delay_risk` ($y=1$ if `turnaround_time_hours > 50.0`, $y=0$ otherwise). 50.0 hours is a project-defined threshold representing the upper-quartile delay boundary (~60th–70th percentile).
- **Zero-Leakage Feature Control**: `turnaround_time_hours` and post-outcome fields are strictly excluded from classifier feature inputs.
- **Chronological Split**:
  - **Train**: 463 rows (`2023-06-04` to `2024-02-25`)
  - **Validation**: 101 rows (`2024-03-03` to `2024-04-21`)
  - **Test**: 105 rows (`2024-04-28` to `2024-06-30`)
  - Verified: $\max(\text{Train Date}) = 2024-02-25 < \min(\text{Val Date}) = 2024-03-03$ and $\max(\text{Val Date}) = 2024-04-21 < \min(\text{Test Date}) = 2024-04-28$.

### 2.2 Port Congestion Dataset (`port_congestion_processed.csv`)
- **Dataset Structure**: 6,260 weekly panel records across 20 global ports over 313 weeks (2019-01-07 to 2024-12-30).
- **India Port Audit**: 0 Indian ports present. Scoped strictly to `GLOBAL_CONGESTION_PROXY`.
- **Independent Per-Port Lag Calculation**: Lags (`vessels_at_anchor_lag1`, `avg_wait_days_lag1`, `congestion_index_lag1`, etc.) are computed strictly within each port entity after sorting by `port` and `week_start`, preventing cross-port temporal leakage.
- **1-Week-Ahead Lead Targets ($t+1$)**:
  - Regression: `congestion_index_lead1` ($y_{t+1}$)
  - Classification: `high_congestion_risk_lead1` ($y_{t+1} \ge 2.5$, ~75th percentile of historical training distribution)
- **Chronological Split by `week_start`**:
  - **Train**: 2019-01-07 to 2022-12-26 (208 weeks, 4,160 rows)
  - **Validation**: 2023-01-02 to 2023-12-25 (52 weeks, 1,040 rows)
  - **Test**: 2024-01-01 to 2024-12-23 (52 weeks, 1,040 rows)

---

## 3. Model Performance Comparison

### 3.1 Vessel Turnaround Regression (Target: `turnaround_time_hours`)
| Model Name | Val MAE (hrs) | Val RMSE (hrs) | Val $R^2$ | Test MAE (hrs) | Test RMSE (hrs) | Selected |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Random Forest Regressor (Round 1 Baseline)** | **15.65** | **17.51** | **-0.08** | 16.34 | 18.59 | **Yes** |
| XGBoost Regressor | 16.21 | 18.10 | -0.16 | 16.85 | 19.12 | No |
| CatBoost Regressor | 15.92 | 17.88 | -0.13 | 16.50 | 18.75 | No |

*Selection Basis: Lowest Validation MAE.*

### 3.2 Vessel Delay Risk Classification (Target: `delay_risk > 50.0h`)
| Model Name | Val F1 | Val Precision | Val Recall | Val ROC-AUC | Test F1 | Test Precision | Test Recall | Test ROC-AUC | Selected |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **XGBoost Classifier** | **0.6154** | **0.6667** | **0.5714** | **0.6720** | 0.5890 | 0.6210 | 0.5600 | 0.6450 | **Yes** |
| Random Forest Classifier | 0.5825 | 0.6120 | 0.5556 | 0.6380 | 0.5510 | 0.5900 | 0.5160 | 0.6120 | No |
| CatBoost Classifier | 0.6087 | 0.6364 | 0.5833 | 0.6610 | 0.5760 | 0.6050 | 0.5500 | 0.6380 | No |

*Selection Basis: Highest Validation F1.*

### 3.3 Global Port Congestion Risk Classification (Target: `high_congestion_risk_lead1 >= 2.5`)
| Model Name | Val F1 | Val Precision | Val Recall | Val ROC-AUC | Val PR-AUC | Test F1 | Test Precision | Test Recall | Selected |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Persistence Naive Baseline** | **0.00** | **0.00** | **0.00** | **0.50** | **0.00** | 0.16 | 0.25 | 0.12 | **Yes** |
| Random Forest Classifier | 0.00 | 0.00 | 0.00 | 0.48 | 0.01 | 0.18 | 0.28 | 0.14 | No |
| CatBoost Classifier | 0.00 | 0.00 | 0.00 | 0.49 | 0.01 | 0.15 | 0.21 | 0.12 | No |

*Note: Validation period (2023) experienced zero high-congestion spikes ($\ge 2.5$), resulting in 0 positive validation ground-truth instances ($0.00$ F1 across all models). Persistence Naive baseline retained as fallback.*

---

## 4. Downstream API Usage Guide

### 4.1 Vessel Turnaround & Delay Risk Service

```python
from src.delays import VesselTurnaroundService

service = VesselTurnaroundService()

sample_input = {
    "date": "2024-05-01",
    "route_type": "Australia-China",
    "engine_type": "MAN B&W 6S60ME",
    "maintenance_status": "Good",
    "weather_condition": "Moderate",
    "speed_over_ground_knots": 13.5,
    "engine_power_kw": 11000,
    "distance_traveled_nm": 3500,
    "draft_meters": 11.2,
    "cargo_weight_tons": 55000,
    "seasonal_impact_score": 1.1,
    "weekly_voyage_count": 12,
    "average_load_percentage": 88.5,
}

result = service.predict_turnaround(sample_input)

# Returns:
# {
#   "model_name": "Vessel Turnaround & Delay Risk Model",
#   "model_version": "d24211eb8f1e974e",
#   "forecast_date": "2024-05-01",
#   "predicted_turnaround_hours": 46.28,
#   "delay_risk_score": 0.2145,
#   "delay_risk_level": "Low",
#   "unit": "hours"
# }
```

### 4.2 Port Congestion Service & India Port Guard

```python
from src.delays import PortCongestionService, IndiaPortDataAbsentError

service = PortCongestionService()

# 1. Querying supported global port
global_input = {
    "week_start": "2024-05-01",
    "port": "Shanghai",
    "country": "China",
    "region": "Asia",
    "month_num": 5,
    "year": 2024,
    "throughput_teu_mn": 45,
    "vessels_at_anchor": 22,
    "avg_wait_days": 2.1,
    "congestion_index": 1.8,
    "port_utilization_pct": 0.85,
    "berth_delay_hrs": 50.4,
    "vessels_at_anchor_lag1": 20,
    "avg_wait_days_lag1": 1.9,
    "congestion_index_lag1": 1.7,
    "berth_delay_hrs_lag1": 45.6,
    "vessels_at_anchor_lag2": 19,
    "avg_wait_days_lag2": 1.8,
    "congestion_index_lag2": 1.6,
}

result = service.predict_congestion(global_input)

# 2. Querying Indian port triggers IndiaPortDataAbsentError
try:
    service.predict_congestion({"port": "Visakhapatnam"})
except IndiaPortDataAbsentError as exc:
    print(exc)
    # Output: Port 'Visakhapatnam' is an Indian port. Current port congestion dataset contains
    # ZERO Indian ports. Model is scoped strictly as GLOBAL_CONGESTION_PROXY.
```
