# FreightWise Round 2 — Stage 1 Data Lineage & Aggregation Architecture

This document describes the end-to-end data lineage, transformation pipelines, schema contracts, and explicit temporal aggregation join rules for FreightWise Stage 1.

---

## 1. Raw-to-Processed Data Lineage

```
[RAW DATA SOURCES]
├── shipping_rates.csv (300 rows) ───────────────> data/processed/freight_rates.csv
├── commodity_prices_supply_chain.csv (110k) ───> data/processed/commodity_prices_processed.csv
├── oil_geopolitics_dataset_2010_2026.csv ─────> data/processed/oil_geopolitics_processed.csv
├── port_congestion.csv (6,260 rows) ───────────> data/processed/port_congestion_processed.csv
├── trade_flows.csv (1,250 rows) ───────────────> data/processed/trade_flows_processed.csv
├── Ship_Performance_Dataset.csv (2,736 rows) ─> data/processed/vessel_performance_processed.csv
└── india/trade/*.xls (5 files) ────────────────> data/processed/india_bulk_imports_2022_2026.csv
                                                           │
                                                           ▼
[MONTHLY FEATURE MERGE PIPELINE]
Merge (Freight + Oil + Coal) ───────────────────> data/processed/monthly_freight_ml.csv (179 rows)
                                                           │
                                                           ▼
Lags (1,3,6,12), Rolling (3,6,12), Sin/Cos ────> data/processed/freight_model_features.csv (167 rows)
                                                           │
                                                           ▼
[STAGE 1 DATALOADER PACKAGE]
src/data/loader.py (10 DataLoader targets) ────> Clean DataFrame Copies & Schema Contracts
                                                           │
                                                           ▼
[ROUND 1 XGBOOST FORECASTING MODEL]
ml/forecasting/final_xgboost_model.joblib ─────> Model Predictions (26 features)
```

---

## 2. Safe Temporal Aggregation & Join Rules

To prevent accidental many-to-many join explosions (fan-out errors):

### Rule 1: Daily Market Data Aggregation
Daily datasets (`oil_geopolitics_processed.csv`) must be aggregated to monthly granularity before joining with monthly freight rates.
- **Function**: `src.data.joins.aggregate_daily_oil_to_monthly()`
- **Aggregation Logic**:
  - `brent_price`, `wti_price`: Monthly mean & month-end price
  - `dxy_index`, `vix`, `gpr_index`, `volatilities`: Monthly mean
  - `event_severity`, `event_flag`: Monthly maximum

### Rule 2: Weekly Port Congestion Aggregation
Weekly datasets (`port_congestion_processed.csv`) must be aggregated to monthly granularity per port/region before joining.
- **Function**: `src.data.joins.aggregate_weekly_congestion_to_monthly()`
- **Aggregation Logic**: Group by `year_month`, `port`, `country`, `region` computing monthly average congestion index, wait days, and berth delay.

### Rule 3: 1-to-1 Monthly Join Protection
- **Function**: `src.data.joins.safe_join_monthly_freight_with_market()`
- **Guards**: Asserts uniqueness on join key (`year_month`) and verifies output row count does not exceed input freight row count.

---

## 3. Explicit Entity & Commodity Normalization Strategy

- **Country Normalization**: Textual variants in raw trade files (`U S A`, `U ARAB EMTS`, `U K`, `SOUTH AFRICA`, `CHINA P RP`) are normalized to standard names (`USA`, `UAE`, `UK`, `South Africa`, `China`) in DataFrame copies.
- **Port Normalization**: Indian import port text variants (`VISAKHAPATNAM SEA`, `PARADIP SEA`, `NHAVA SHEVA SEA`) normalized to canonical port names (`Visakhapatnam Port`, `Paradip Port`, `Nhava Sheva Port`).
- **Canonical Commodity Distinction**: `COAL,COKE AND BRIQUITTES ETC` (Indian import trade category) and `Thermal Coal Newcastle` (international market price benchmark) are strictly maintained as separate canonical concepts.
