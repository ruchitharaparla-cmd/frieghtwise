# FreightWise Round 2 — Stage 1 Data Quality Audit Report

**Generated**: 2026-09-05T15:04:31.624794  
**Total Datasets Audited**: 10  

## Summary of Dataset Quality

| Dataset Name | Rows | Columns | Duplicate Rows | Missing Columns | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `freight_rates` | 300 | 12 | 0 | 2 | **WARNINGS_FLAGGED** |
| `commodity_prices` | 1,176 | 10 | 0 | 0 | **PASSED** |
| `oil_geopolitics` | 4,047 | 27 | 0 | 0 | **PASSED** |
| `port_congestion` | 6,260 | 14 | 0 | 0 | **PASSED** |
| `trade_flows` | 1,250 | 14 | 0 | 1 | **WARNINGS_FLAGGED** |
| `vessel_performance` | 2,736 | 22 | 0 | 5 | **WARNINGS_FLAGGED** |
| `india_bulk_imports` | 11,200 | 14 | 0 | 0 | **PASSED** |
| `monthly_freight_ml` | 179 | 21 | 0 | 0 | **PASSED** |
| `freight_model_features` | 167 | 47 | 0 | 0 | **PASSED** |
| `route_demand_summary` | 40 | 7 | 0 | 0 | **PASSED** |

## Detailed Missing Values & Quality Flags

### Dataset: `freight_rates`
- **Rows**: 300, **Columns**: 12
- **Duplicates**: 0
- **Missing Value Details**:
  - `bdi_mom_change_pct`: 1 missing (0.33%)
  - `container_yoy_pct`: 12 missing (4.0%)
- **Date Coverage**:
  - `date`: 2000-01-01 to 2024-12-01 (300 unique dates)
  - `year`: 1970-01-01 to 1970-01-01 (25 unique dates)
  - `month`: 1970-01-01 to 1970-01-01 (12 unique dates)
  - `bulk_carrier_handysize_usd_day`: 1970-01-01 to 1970-01-01 (290 unique dates)
  - `tanker_rate_aframax_usd_day`: 1970-01-01 to 1970-01-01 (291 unique dates)
  - `on_time_delivery_pct`: 1970-01-01 to 1970-01-01 (1 unique dates)
  - `year_month`: 2000-01-01 to 2024-12-01 (300 unique dates)
  - `canonical_month_start`: 2000-01-01 to 2024-12-01 (300 unique dates)

### Dataset: `commodity_prices`
- **Rows**: 1,176, **Columns**: 10
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
- **Date Coverage**:
  - `date`: 2010-01-01 to 2026-04-01 (196 unique dates)
  - `year`: 1970-01-01 to 1970-01-01 (17 unique dates)
  - `month`: 1970-01-01 to 1970-01-01 (12 unique dates)
  - `year_month`: 2010-01-01 to 2026-04-01 (196 unique dates)
  - `canonical_month_start`: 2010-01-01 to 2026-04-01 (196 unique dates)

### Dataset: `oil_geopolitics`
- **Rows**: 4,047, **Columns**: 27
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
- **Date Coverage**:
  - `date`: 2010-02-17 to 2026-03-12 (4047 unique dates)
  - `year`: 1970-01-01 to 1970-01-01 (17 unique dates)
  - `month`: 1970-01-01 to 1970-01-01 (12 unique dates)
  - `year_month`: 2010-02-01 to 2026-03-01 (194 unique dates)
  - `canonical_month_start`: 2010-02-01 to 2026-03-01 (194 unique dates)

### Dataset: `port_congestion`
- **Rows**: 6,260, **Columns**: 14
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
- **Date Coverage**:
  - `year`: 1970-01-01 to 1970-01-01 (6 unique dates)
  - `month`: 2019-01-01 to 2024-12-01 (72 unique dates)
  - `avg_wait_days`: 1970-01-01 to 1970-01-01 (254 unique dates)
  - `year_month`: 2019-01-01 to 2024-12-01 (72 unique dates)
  - `canonical_month_start`: 2019-01-01 to 2024-12-01 (72 unique dates)

### Dataset: `trade_flows`
- **Rows**: 1,250, **Columns**: 14
- **Duplicates**: 0
- **Missing Value Details**:
  - `yoy_growth_pct`: 50 missing (4.0%)
- **Date Coverage**:
  - `year`: 1970-01-01 to 1970-01-01 (25 unique dates)
  - `year_month`: 2000-01-01 to 2024-01-01 (25 unique dates)

### Dataset: `vessel_performance`
- **Rows**: 2,736, **Columns**: 22
- **Duplicates**: 0
- **Missing Value Details**:
  - `ship_type`: 136 missing (4.97%)
  - `route_type`: 136 missing (4.97%)
  - `engine_type`: 136 missing (4.97%)
  - `maintenance_status`: 136 missing (4.97%)
  - `weather_condition`: 136 missing (4.97%)
- **Date Coverage**:
  - `date`: 2023-06-04 to 2024-06-30 (57 unique dates)
  - `year`: 1970-01-01 to 1970-01-01 (2 unique dates)
  - `month`: 1970-01-01 to 1970-01-01 (12 unique dates)
  - `turnaround_time_hours`: 1970-01-01 to 1970-01-01 (60 unique dates)
  - `year_month`: 2023-06-01 to 2024-06-01 (13 unique dates)
  - `canonical_month_start`: 2023-06-01 to 2024-06-01 (13 unique dates)

### Dataset: `india_bulk_imports`
- **Rows**: 11,200, **Columns**: 14
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
- **Date Coverage**:
  - `Year`: 1970-01-01 to 1970-01-01 (5 unique dates)
  - `Period_Start`: 2022-01-01 to 2026-01-01 (5 unique dates)
  - `year_month`: 2022-01-01 to 2026-01-01 (5 unique dates)
  - `canonical_month_start`: 2022-01-01 to 2026-01-01 (5 unique dates)

### Dataset: `monthly_freight_ml`
- **Rows**: 179, **Columns**: 21
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
- **Date Coverage**:
  - `date`: 2010-02-01 to 2024-12-01 (179 unique dates)
  - `bulk_carrier_handysize_usd_day`: 1970-01-01 to 1970-01-01 (172 unique dates)
  - `tanker_rate_aframax_usd_day`: 1970-01-01 to 1970-01-01 (172 unique dates)
  - `on_time_delivery_pct`: 1970-01-01 to 1970-01-01 (1 unique dates)
  - `year_month`: 2010-02-01 to 2024-12-01 (179 unique dates)
  - `canonical_month_start`: 2010-02-01 to 2024-12-01 (179 unique dates)

### Dataset: `freight_model_features`
- **Rows**: 167, **Columns**: 47
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
- **Date Coverage**:
  - `date`: 2011-02-01 to 2024-12-01 (167 unique dates)
  - `bulk_carrier_handysize_usd_day`: 1970-01-01 to 1970-01-01 (160 unique dates)
  - `tanker_rate_aframax_usd_day`: 1970-01-01 to 1970-01-01 (160 unique dates)
  - `on_time_delivery_pct`: 1970-01-01 to 1970-01-01 (1 unique dates)
  - `year_month`: 2011-02-01 to 2024-12-01 (167 unique dates)
  - `month_num`: 1970-01-01 to 1970-01-01 (12 unique dates)
  - `month_sin`: 1969-12-31 to 1970-01-01 (3 unique dates)
  - `month_cos`: 1969-12-31 to 1970-01-01 (3 unique dates)
  - `canonical_month_start`: 2011-02-01 to 2024-12-01 (167 unique dates)

### Dataset: `route_demand_summary`
- **Rows**: 40, **Columns**: 7
- **Duplicates**: 0
- **Missing Values**: None (0.00%)
