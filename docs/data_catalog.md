# FreightWise Round 2 — Stage 1 Data Catalog

This catalog documents the **10 Stage 1 DataLoader targets** and raw data assets available in the FreightWise repository.

---

## 1. Stage 1 DataLoader Targets Summary

| Target Dataset Name | File Path | Granularity | Rows | Cols | Primary Key / Join Key | Classification | Status |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| **Freight Rates** | `data/processed/freight_rates.csv` | Monthly | 300 | 10 | `date`, `year_month` | Class A | Verified |
| **Commodity Prices** | `data/processed/commodity_prices_processed.csv` | Monthly | 1,176 | 8 | `date`, `commodity` | Class A | Verified |
| **Oil & Geopolitics** | `data/processed/oil_geopolitics_processed.csv` | Daily | 4,047 | 25 | `date`, `year_month` | Class A | Verified |
| **Port Congestion** | `data/processed/port_congestion_processed.csv` | Weekly | 6,260 | 12 | `week_start`, `port` | Class B | `GLOBAL_CONGESTION_PROXY` |
| **Trade Flows** | `data/processed/trade_flows_processed.csv` | Annual | 1,250 | 13 | `year`, `exporter`, `importer` | Class B | Verified |
| **Vessel Performance** | `data/processed/vessel_performance_processed.csv` | Voyage/Daily | 2,736 | 20 | `date`, `ship_type` | Class A | Verified (669 Bulk Carrier) |
| **India Bulk Imports** | `data/processed/india_bulk_imports_2022_2026.csv` | Monthly Periodic | 11,200 | 10 | `Period_Start`, `Port`, `Commodity` | Class A | Verified (100% TON) |
| **Monthly Freight ML** | `data/processed/monthly_freight_ml.csv` | Monthly | 179 | 20 | `date`, `year_month` | Class A | Verified |
| **Freight Model Features**| `data/processed/freight_model_features.csv` | Monthly | 167 | 46 | `date`, `year_month` | Class A | Verified (46 cols) |
| **Route Demand Summary** | `data/processed/route_demand_summary.csv` | Route Summary | 40 | 7 | `Country_of_Consignment`, `Port` | Class A | `HISTORICAL_DEMAND_NOT_FORECAST` |

---

## 2. Detailed Dataset Specifications

### 2.1 Freight Model Features (`freight_model_features.csv`)
- **Rows**: 167 (Feb 2011 – Dec 2024)
- **Columns**: 46
- **Target Variable**: `bulk_carrier_handysize_usd_day` (Handysize Bulk Carrier charter rate in USD/day)
- **Key Feature Categories**:
  - Target & Lags: `freight_lag_1`, `3`, `6`, `12`
  - Rolling Windows: `freight_rolling_mean_3`, `6`, `12`, `freight_rolling_std_3`
  - Market Indicators: `baltic_dry_index`, `tanker_rate_aframax_usd_day`, `supply_chain_pressure_index`, `on_time_delivery_pct`, `bdi_mom_change_pct`, `container_yoy_pct`
  - Geopolitical/Oil: `brent_price`, `wti_price`, `dxy_index`, `vix`, `gpr_index`, `brent_volatility_30d`, `wti_volatility_30d`, `brent_wti_spread`, `event_severity`, `event_flag`
  - Commodity: `thermal_coal_price`, `thermal_coal_price_lag_1`, `thermal_coal_price_lag_3`
  - Temporal Encodings: `month_num`, `quarter`, `month_sin`, `month_cos`

### 2.2 Vessel Performance Dataset (`vessel_performance_processed.csv`)
- **Rows**: 2,736 total (669 Bulk Carrier, 653 Fish Carrier, 643 Tanker, 635 Container Ship, 136 Missing categoricals)
- **Columns**: 20
- **Units**: Speed (`knots`), Engine Power (`kW`), Distance (`nm`), Draft (`meters`), Cargo Weight (`tons`), Operational Cost (`USD`), Revenue (`USD`), Turnaround (`hours`).
- **Usage**: Bulk Carrier subset (669 rows) is used for training CatBoost/XGBoost turnaround time and delay models in Stage 3.

### 2.3 India Bulk Imports (`india_bulk_imports_2022_2026.csv`)
- **Rows**: 11,200 periodic import records (Jan 2022 – May 2026)
- **Commodity Categories (6)**: Petroleum Products (5,531), Fertilizers Manufactured (2,224), Coal/Coke/Briquettes (1,661), Petroleum Crude (826), Fertilizers Crude (729), Iron Ore (229).
- **Units**: `TON` (100% Metric Tons across all 11,200 rows).
- **Total Volume**: 2.38 Billion Metric Tons ($948.67 Billion USD).
- **Normalization**: Text variants normalized in copies (`U S A` -> `USA`, `U ARAB EMTS` -> `UAE`, `VISAKHAPATNAM SEA` -> `Visakhapatnam Port`). `COAL,COKE AND BRIQUITTES ETC` retained as distinct canonical concept from `Thermal Coal Newcastle`.

### 2.4 Port Congestion (`port_congestion_processed.csv`)
- **Rows**: 6,260 weekly records (20 ports, 13 countries, Jan 2019 – Dec 2024)
- **Status Tag**: `GLOBAL_CONGESTION_PROXY`
- **Indian Ports Present**: **ZERO (0)**. Serves as global supply chain disruption proxy only.

### 2.5 Indian Port Physical Constraints (`port_details.csv`)
- **Status Tag**: `NOT_AVAILABLE_IN_CURRENT_DATASET`
- **Finding**: File contains headers but zero usable data rows. Physical constraint checks (LOA, beam, max draft, DWT, berth length) marked as non-evaluable until enriched in Stage 4.
