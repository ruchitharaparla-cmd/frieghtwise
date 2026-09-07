# FreightWise Stage 5: Cost & Risk Calculation Engine
## Detailed Implementation Plan

**Status:** Planning Phase  
**Date:** 2026-09-07  
**Branch:** stage5-cost-risk  
**Scope:** Deterministic cost and risk calculation from verified Stage 1-4 data  

---

## 1. Executive Summary

Stage 5 implements a **transparent, deterministic, and data-honest** cost and risk calculation engine. The engine consumes verified outputs from previous stages and produces structured voyage-level cost and risk information.

**Core Principle:** NEVER fabricate numerical data. If a component is unavailable, explicitly represent it as such rather than assuming zero.

**Key Design Decision:** Stage 5 is NOT a decision-making engine. It is a calculation engine. All numerical decisions (threshold selection, missing-value defaults) are delegated to Stage 6 (optimization) or made at configuration time by project stakeholders.

---

## 2. Current State Assessment

### 2.1 Available Data Sources

#### Data Type 1: Vessel Performance (Processed)
**Source:** `/data/processed/vessel_performance_processed.csv`  
**Records:** ~2,737  
**Date Range:** June–December 2023, 2024  
**Key Cost-Relevant Fields:**
- `operational_cost_usd`: Verified vessel operating cost per voyage
- `revenue_per_voyage_usd`: Charter revenue (can infer cost structure)
- `turnaround_time_hours`: Actual historical turnaround
- `cargo_weight_tons`: Cargo quantity processed
- `speed_over_ground_knots`: Operational speed
- `engine_power_kw`: Power consumption (fuel intensity)
- `weather_condition`: Operational weather impact
- `seasonal_impact_score`: Seasonal cost modifier
- `route_type`: Short-haul, Long-haul, Transoceanic
- `maintenance_status`: Good, Fair, Critical (affects operational cost)

**Data Honesty:** ✅ Actual observed costs. Can extract cost/tonne metrics.  
**Granularity:** Daily records by vessel type and route. Not at vessel-class level; aggregated by ship type.

#### Data Type 2: Freight Rates (Historical)
**Source:** `/data/processed/freight_rates.csv`  
**Records:** ~301  
**Date Range:** January 2000 – December 2024 (monthly)  
**Key Cost-Relevant Fields:**
- `baltic_dry_index`: Market sentiment (dry bulk shipping rate index)
- `bulk_carrier_handysize_usd_day`: Actual handysize bulk carrier charter rate (USD/day)
- `tanker_rate_aframax_usd_day`: Aframax tanker charter rate (USD/day)
- `supply_chain_pressure_index`: Macro supply-chain stress indicator
- `on_time_delivery_pct`: Historical on-time delivery rate
- `bdi_mom_change_pct`: Baltic Dry Index month-over-month change
- `container_yoy_pct`: Container market year-over-year change

**Data Honesty:** ✅ Observable market rates. Can use to infer freight costs or charter daily costs.  
**Limitation:** Does not contain:
- Indian East Coast specific rates
- Oil/bunker prices
- Port-specific handling charges
- Demurrage or detention rates
- Insurance rates

#### Data Type 3: Port Congestion (Historical)
**Source:** `/data/processed/port_congestion_processed.csv`  
**Records:** ~6,261  
**Date Range:** Weekly, 2019–2024  
**Key Cost-Relevant Fields:**
- `avg_wait_days`: Average vessel waiting time
- `berth_delay_hrs`: Berth delay in hours
- `congestion_index`: Normalized congestion score (0–1 scale)
- `port_utilization_pct`: Port utilization percentage
- `port`: Global port names (Antwerp, Guangzhou, Hong Kong, Ningbo, Rotterdam, Shanghai, Singapore, Busan, etc.)
- `country`, `region`: Port geography

**Data Honesty:** ✅ Actual observed waiting times and delays.  
**Limitation:** Does NOT include Indian East Coast ports. Cannot provide India-specific port delays.

#### Data Type 4: Commodity Prices (Historical)
**Source:** `/data/processed/commodity_prices_processed.csv`  
**Records:** ~11,000  
**Date Range:** Daily to monthly, 2010–2026  
**Key Fields:**
- `commodity`: Specific commodities (e.g., Wheat, Oil, Iron Ore, Coal, etc.)
- `category`: Commodity classification
- `unit`: Price unit (bushel, barrel, tonne, etc.)
- `currency`: USD typically
- `average_price`: Daily/monthly average price

**Data Honesty:** ✅ Observable commodity market prices.  
**Limitation:** Does not capture cargo-specific loading/unloading charges or commodity surcharges at ports.

#### Data Type 5: Oil & Geopolitics (Historical)
**Source:** `/data/processed/oil_geopolitics_processed.csv`  
**Records:** ~4,700+  
**Date Range:** Daily, 2010–2026  
**Key Fields:**
- `brent_price`: Brent crude oil price (USD/barrel)
- `wti_price`: WTI crude oil price
- `dxy_index`: US Dollar Index (currency volatility)
- `vix`: Volatility Index (market volatility)
- `gpr_index`: Geopolitical Risk Index
- `event_type`, `event_severity`: Geopolitical event tracking

**Data Honesty:** ✅ Observable market and geopolitical data.  
**Limitation:** Global oil prices, not bunker prices. No direct fuel cost for specific vessel types.

#### Data Type 6: India Bulk Imports (Historical)
**Source:** `/data/processed/india_bulk_imports_2022_2026.csv`  
**Records:** ~1.1M  
**Date Range:** 2022–2026 (Jan–May 2026)  
**Key Fields:**
- `commodity`: Import commodity
- `port`: Indian port destination
- `quantity_tonnes`: Import quantity
- `origin_country`: Country of origin
- `value_usd`: Cargo value

**Data Honesty:** ✅ Actual import statistics from DGCIS.  
**Limitation:** Does not include shipping costs or vessel requirements.

### 2.2 Existing Database Models

#### Freight Model
```
Table: freight_rates
├── freight_rate (NULL-able) — forecast or historical rate
├── confidence (0-1) — forecast confidence
├── data_status ("KNOWN" | "UNAVAILABLE")
└── model_version — model identifier
```

**Pattern:** Missing values represented via `data_status`. This is the pattern Stage 5 should follow.

#### Vessel Model
```
Table: vessels
├── dwt (deadweight tonnes)
├── loa_m, beam_m, draft_m (dimensions)
├── cargo_types (string list)
├── is_available (boolean)
└── data_status
```

**Limitation:** No operating cost per day/tonne. No fuel consumption profile.

#### Voyage Model
```
Table: voyages
├── cargo_type, quantity_tonnes
├── origin_country, destination_region
├── arrival_date
├── charter_start_date, charter_end_date (optional)
└── status ("PLANNED", etc.)
```

**Observation:** Voyage model does not store cost or risk. Stage 5 will calculate these.

#### Port Model
```
Table: ports
├── max_draft_m, max_loa_m, max_beam_m (constraints)
├── annual_capacity_tonnes
├── utilization_percent
├── average_waiting_hours
└── data_status
```

**Limitation:** No port charges, no demurrage rates, no handling surcharges.

#### Prediction Model
```
Table: predictions
├── prediction_type
├── predicted_value (NULL-able)
├── confidence (0-1)
├── data_status ("KNOWN" | "UNAVAILABLE")
└── model_version
```

**Pattern:** Follows same pattern as Freight.

### 2.3 Existing Cost & Risk Services

#### Current cost_service.py
```python
def calculate_cost(
    quantity_tonnes: float,
    freight_rate: Optional[float],
    bunker_cost: Optional[float],
    port_cost: Optional[float],
    expected_delay_hours: Optional[float],
    demurrage_rate_per_day: Optional[float],
):
```

**Assessment:**
- ✅ Correctly returns total_landed_cost=None when any required component is missing
- ❌ Expects pre-computed bunker_cost and port_cost (not calculated)
- ❌ No source tracking for individual costs
- ❌ No cost availability matrix

#### Current risk_service.py
```python
def calculate_risk(
    congestion_score: Optional[float],
    weather_score: Optional[float] = None,
    demurrage_score: Optional[float] = None,
):
```

**Assessment:**
- ✅ Correctly returns data_status="UNAVAILABLE" when all scores are None
- ✅ Thresholds documented (35, 65)
- ❌ Demurrage score must be calculated, not provided
- ❌ No individual component availability tracking

### 2.4 Existing Forecast & Congestion Services

#### forecast_service.py
Returns:
```python
{
    "forecast_rate": float | None,
    "confidence": float | None,
    "data_status": "KNOWN" | "UNAVAILABLE",
    "model_version": str | None
}
```

**Pattern:** Clear contract. Suitable input for Stage 5.

#### congestion_service.py
Returns:
```python
{
    "score": float | None,  # 0-100 scale
    "impact": "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN",
    "data_status": "KNOWN" | "UNAVAILABLE"
}
```

**Pattern:** Clear contract. Suitable input for Stage 5.

### 2.5 Decision Engine Expectations (Stage 6 input)

From `recommendation_service.py` and `optimization_service.py`:

**Required fields per candidate:**
```python
{
    "vessel_id": int,
    "port_id": int,
    "feasible": bool,  # Stage 4 output
    "forecast": dict,  # Stage 2 output
    "cost": dict,      # Stage 5 output (THIS)
    "risk": dict,      # Stage 5 output (THIS)
    "total_landed_cost": float | None,  # Stage 5 aggregation
    "overall_risk": float | None,       # Stage 5 aggregation
    "expected_delay_hours": float | None,  # Stage 5 calculation
    "score": float | None,  # Stage 6 ranking
    "rejection_reasons": list[str]  # Traceability
}
```

**Stage 6 Behavior:**
- Options with `total_landed_cost=None` are ranked last (line: `option["score"] is None`)
- Options with `overall_risk=None` default to 50.0 for scoring
- Options with `expected_delay_hours=None` default to 24.0 for scoring

**Design Implication:** Stage 5 must be explicit about cost/risk availability so Stage 6 can make informed decisions.

---

## 3. Cost Component Analysis

Based on actual available data, Stage 5 can calculate the following:

### 3.1 Definable Cost Components

#### A. Freight Cost (Historical & Forecasted)
**Formula:** `freight_cost = quantity_tonnes * freight_rate_per_tonne`

**Data Source:**
- Historical: `freight_rates.csv` (bulk_carrier_handysize_usd_day)
- Forecasted: Stage 2 ML model output (via forecast_service.py)

**Conversion Logic:**
```
Daily charter rate (USD/day) → Cost per tonne
  = (daily_rate * voyage_duration_days) / cargo_quantity_tonnes

OR use historical operational_cost_usd from vessel_performance:
  = operational_cost_usd / cargo_weight_tons
```

**Data Status:**
- ✅ KNOWN (historical): Direct from freight_rates.csv
- ✅ KNOWN (forecast): From Stage 2 model if confidence > threshold
- ⚠️  PARTIAL: Vessel-class specific rates available (Handysize, Aframax). Other vessel classes require mapping/interpolation.

**Availability States:**
1. `CALCULATED` — Direct from data
2. `FORECASTED` — From ML model with confidence
3. `INTERPOLATED` — Mapped from related vessel class
4. `UNAVAILABLE` — No applicable rate available

---

#### B. Operational/Vessel Cost
**Formula:** `operational_cost = quantity_tonnes * operational_cost_per_tonne`

**Data Source:** `vessel_performance_processed.csv`
- `operational_cost_usd` per voyage
- `cargo_weight_tons` per voyage
- Calculate: `operational_cost_per_tonne = operational_cost_usd / cargo_weight_tons`

**Aggregation by Ship Type:**
- Handysize bulk carrier
- Panamax bulk carrier
- Capesize bulk carrier
- Container ship
- Tanker
- Fish carrier
- Other

**Data Status:**
- ✅ KNOWN: Actual observed costs from historical data
- ⚠️  VESSEL_CLASS_DEPENDENT: Not individual vessel specific; aggregated by type/route

**Historical Analysis (from data):**
- Handysize: ~10–20 USD/tonne (estimated range from aggregated data)
- Vessel-specific efficiency varies by maintenance_status, seasonal_impact_score
- Route impact: Transoceanic > Long-haul > Short-haul

**Availability States:**
1. `CALCULATED` — Historical average by vessel class + route
2. `ADJUSTED` — Adjusted by maintenance status and seasonality
3. `UNAVAILABLE` — No comparable vessel class

---

#### C. Fuel/Energy Cost
**Formula:** `fuel_cost = distance_nm * fuel_consumption_per_nm * bunker_price`

**Data Source:** 
- Distance: `distance_traveled_nm` from vessel_performance.csv
- Fuel consumption: Derived from `engine_power_kw` and `speed_over_ground_knots`
- Bunker price: NOT in processed data (only oil_geopolitics_processed.csv with Brent/WTI, not bunker)

**Calculation Approach:**
```
Fuel consumption (metric tonnes/day) = engine_power_kw / efficiency_factor
Distance over voyage = distance_nm_per_day * voyage_duration_days
Fuel needed = distance / speed * consumption_rate
Fuel cost = fuel_needed * bunker_price_per_tonne
```

**Data Status:**
- ✅ PARTIAL: Engine power and speed available
- ❌ MISSING: Bunker prices (only Brent/WTI crude available, not bunker)
- ⚠️  ESTIMATED: Fuel consumption derived from engine power (not actual consumption logs)

**Availability States:**
1. `UNAVAILABLE_FUEL_PRICE` — Cannot compute without bunker price
2. `ESTIMATED` — Estimated consumption + proxy fuel price
3. `NOT_CALCULABLE` — Insufficient parameters

**Design Decision:** Given lack of bunker price data, Stage 5 should:
- Flag `fuel_cost` as unavailable/estimated
- Store engine_power_kw, distance, speed as intermediate values
- Defer fuel cost calculation to Stage 6 if Stage 6 has bunker price data
- OR document that bunker cost assumption must be provided externally

---

#### D. Port/Handling Cost
**Formula:** `port_cost = cargo_tonnes * handling_rate_per_tonne`

**Data Source:** NOT AVAILABLE in processed data
- Port model has `utilization_percent` but NOT charges
- Port congestion model has waiting time but NOT charges
- Commodity prices available but NOT port-specific handling surcharges

**Estimation Approach (if needed):**
- Industry standard: ~5-15 USD/tonne handling (varies by port type and cargo)
- Port utilization correlates with congestion surcharge

**Data Status:**
- ❌ NOT AVAILABLE: No port charge data in dataset
- ⚠️  COULD_BE_ESTIMATED: If Stage 6 provides external port charge data
- ⚠️  COULD_BE_CORRELATED: With port utilization, but not direct

**Availability States:**
1. `UNAVAILABLE` — No data
2. `EXTERNAL_PROVIDED` — Provided by Stage 6 or external system
3. `ESTIMATED_FROM_UTILIZATION` — Derived from port utilization (if formula defined)

**Design Decision:** Stage 5 should:
- NOT fabricate port costs
- Provide mechanism for Stage 6 to supply port costs
- Track port utilization as a risk/cost proxy

---

#### E. Delay-Related Cost (Expected Demurrage)
**Formula:** `delay_cost = delay_hours / 24 * demurrage_rate_per_day`

**Data Source:**
- Delay hours: From congestion service (berth_delay_hrs, avg_wait_days)
- Demurrage rate: NOT AVAILABLE in dataset

**Calculation Approach:**
```
Expected delay hours = (avg_wait_days * 24) + berth_delay_hrs
Demurrage rate = daily charter rate * (1 + demurrage_surcharge_pct)
  OR fixed rate (depends on charter party)
Delay cost = (expected_delay_hours / 24) * demurrage_rate
```

**Data Status:**
- ✅ PARTIAL: Delay hours available from congestion model
- ❌ MISSING: Demurrage rates (not in data)
- ⚠️  DERIVABLE: Could infer from charter rates with assumptions

**Availability States:**
1. `CALCULATED` — With available delay hours and demurrage rate
2. `PARTIAL_DELAY_ONLY` — Only delay hours available (demurrage rate missing)
3. `UNAVAILABLE_DEMURRAGE_RATE` — No demurrage rate available

**Design Decision:** Stage 5 should:
- Calculate delay_hours from congestion model
- Accept demurrage_rate as a parameter (from Stage 6 config or external)
- Return delay_hours and demurrage_cost separately with status

---

#### F. Congestion-Related Cost (Variable Surcharge)
**Formula:** `congestion_surcharge = base_cost * congestion_surcharge_multiplier`

**Data Source:**
- Congestion index: 0–1 scale from port_congestion_processed.csv
- Base multiplier: NOT DEFINED (project-specific)

**Calculation Approach:**
```
congestion_index ∈ [0, 1]
surcharge_multiplier = 1.0 + (congestion_index * surcharge_factor)
  where surcharge_factor is project-defined (e.g., 0.05 = 5% max surcharge)
```

**Data Status:**
- ✅ KNOWN: Congestion index available
- ❓ NOT_DEFINED: Surcharge multiplier (project decision)

**Availability States:**
1. `CALCULATED` — With defined surcharge factor
2. `NOT_CALCULATED_THRESHOLD_UNDEFINED` — Congestion index available but multiplier not defined

**Design Decision:** Stage 5 should:
- Store congestion_index as a cost modifier input
- Accept surcharge_factor as a config parameter
- Document thresholds explicitly (no implicit assumptions)
- Stage 6 or project stakeholders define factor

---

### 3.2 Summary Table: Definable vs. Unavailable Costs

| Component | Available Data | Missing Data | Stage 5 Approach |
|---|---|---|---|
| **Freight Cost** | Historical rates, ML forecasts | Rate per vessel class mapping | Calculate from available rates; flag vessel class mapping status |
| **Operational Cost** | Historical cost/tonne by ship type | Specific vessel cost | Calculate by ship type; note vessel-class dependency |
| **Fuel Cost** | Engine power, speed, distance | Bunker prices, actual consumption | Flag as unavailable; provide intermediate values for Stage 6 |
| **Port Cost** | Port utilization | Handling charges, surcharges | Flag as unavailable; accept external provision |
| **Delay Cost** | Congestion/berth delay hours | Demurrage rates | Calculate delay hours; require demurrage_rate parameter |
| **Congestion Surcharge** | Congestion index | Surcharge factor | Flag as unavailable until factor defined |
| **Insurance** | None | Insurance rates | NOT CALCULATED |
| **Other Costs** | None | Taxes, documentation, etc. | NOT CALCULATED |

---

## 4. Risk Component Analysis

Based on available data, Stage 5 can identify the following risk signals:

### 4.1 Definable Risk Components

#### A. Congestion Risk
**Formula:** `congestion_risk_score = congestion_index * 100`

**Data Source:** `port_congestion_processed.csv` → `congestion_index` (0–1 scale)

**Interpretation (Project-Defined):**
```
0.0 ≤ congestion_index < 0.33  → LOW congestion risk
0.33 ≤ congestion_index < 0.66 → MEDIUM congestion risk
0.66 ≤ congestion_index ≤ 1.0  → HIGH congestion risk
```

**Associated Metrics:**
- `avg_wait_days`: Average vessel waiting time
- `berth_delay_hrs`: Berth delay in hours
- `port_utilization_pct`: Port utilization percentage
- `vessels_at_anchor`: Number of vessels waiting

**Data Status:**
- ✅ KNOWN: Historical congestion data available
- ⚠️  FORECAST_UNAVAILABLE: No future congestion forecast (Stage 3 should provide)

**Availability States:**
1. `KNOWN` — Historical/current congestion data available
2. `FORECASTED` — Future congestion from Stage 3 model
3. `UNAVAILABLE` — No congestion data

---

#### B. Delay Risk
**Formula:** `delay_risk_hours = avg_wait_days * 24 + berth_delay_hrs`

**Data Source:** `port_congestion_processed.csv`

**Risk Interpretation:**
```
delay_risk_hours < 48    → LOW delay risk
48 ≤ delay_risk_hours < 144 → MEDIUM delay risk
delay_risk_hours ≥ 144   → HIGH delay risk
```

**Data Status:**
- ✅ KNOWN: Historical waiting times available
- ⚠️  FORECAST_REQUIRED: Stage 3 should predict future delays

---

#### C. Weather Risk
**Formula:** `weather_risk_score` derived from route/season

**Data Source:**
- `vessel_performance_processed.csv`: `weather_condition` (Calm, Moderate, Rough)
- `seasonal_impact_score`: Seasonal cost/risk modifier
- Route type: Short-haul, Long-haul, Transoceanic
- Month/season: Monsoon seasons, storm patterns

**Risk Interpretation:**
```
Calm → LOW
Moderate → MEDIUM
Rough → HIGH

+ seasonal adjustment
+ route hazard (Transoceanic > Long-haul > Short-haul)
```

**Data Status:**
- ✅ PARTIAL: Historical weather conditions available by date
- ⚠️  FORECAST_REQUIRED: Future weather forecast not in dataset

**Availability States:**
1. `HISTORICAL_PATTERN` — Based on seasonal/historical patterns
2. `FORECAST` — Based on weather forecast (external)
3. `UNAVAILABLE` — No data

---

#### D. Market Volatility Risk
**Formula:** `volatility_risk_score` from freight market indicators

**Data Source:** `freight_rates.csv`
- `bdi_mom_change_pct`: Baltic Dry Index month-over-month change
- `container_yoy_pct`: Container market year-over-year change
- Volatility indicator: Standard deviation or coefficient of variation

**Also from oil_geopolitics_processed.csv:**
- `vix`: Volatility Index (market volatility)
- `gpr_index`: Geopolitical Risk Index

**Risk Interpretation:**
```
Volatility Score = f(BDI volatility, commodity volatility, VIX, GPR)
Low < 30 → LOW risk
30-60 → MEDIUM risk
> 60 → HIGH risk
```

**Data Status:**
- ✅ KNOWN: Historical volatility indicators available
- ⚠️  FORECAST_REQUIRED: Future market volatility unknown

---

#### E. Geopolitical Risk
**Formula:** `geopolitical_risk_score` from GPR index and event tracking

**Data Source:** `oil_geopolitics_processed.csv`
- `gpr_index`: Geopolitical Risk Index
- `event_type`, `event_severity`: Geopolitical event tracking

**Risk Interpretation:**
```
gpr_index ∈ [0, 200+]
Low: < 100 → LOW risk
Medium: 100-150 → MEDIUM risk
High: > 150 → HIGH risk

+ event_severity modifier for active events
```

**Data Status:**
- ✅ KNOWN: Historical GPR index available
- ⚠️  FORECAST_REQUIRED: Future geopolitical risk speculative

---

#### F. Commodity Price Volatility
**Formula:** `commodity_volatility_score` from price fluctuations

**Data Source:** `commodity_prices_processed.csv`

**Calculation Approach:**
```
For each commodity:
  price_std = standard_deviation(prices_last_3_months)
  price_mean = mean(prices_last_3_months)
  volatility_pct = price_std / price_mean * 100

volatility_pct < 5 → LOW
5-15 → MEDIUM
> 15 → HIGH
```

**Data Status:**
- ✅ KNOWN: Historical commodity prices available
- ⚠️  COMMODITY_SPECIFIC: Only for tracked commodities

---

### 4.2 Risk Components NOT Calculated

#### NOT Included (Missing Data):
- **Bunker/Fuel Price Risk:** No bunker price data
- **Currency Risk:** No foreign exchange forecasts
- **Vessel-Specific Risk:** No vessel condition history beyond maintenance_status
- **Insurance/Claim Risk:** No insurance data
- **Regulatory/Documentation Risk:** No regulatory data
- **Cargo Damage Risk:** No cargo-specific risk data

**Design Decision:** These risks should either:
1. Be flagged as unavailable
2. Be calculated externally by Stage 6
3. Be represented as "unknown" in risk summary

---

### 4.3 Summary Table: Risk Components

| Risk Component | Data Available | Calculation Status | Notes |
|---|---|---|---|
| **Congestion** | ✅ YES | Fully calculable | Port-specific; global data (not India) |
| **Delay** | ✅ YES | Fully calculable | Derivable from congestion data |
| **Weather** | ✅ PARTIAL | Historical patterns only | Forecast required for future risk |
| **Market Volatility** | ✅ YES | Fully calculable | From BDI, commodity prices, VIX |
| **Geopolitical** | ✅ PARTIAL | GPR index available | Event-based; forecast uncertain |
| **Commodity Price** | ✅ YES | Fully calculable | Price volatility from time series |
| **Bunker Price** | ❌ NO | Not calculable | Brent/WTI != Bunker; missing |
| **Currency** | ❌ NO | Not calculable | Not in data |
| **Vessel Condition** | ✅ PARTIAL | Maintenance status only | Limited to historical patterns |
| **Regulatory** | ❌ NO | Not calculable | Not tracked |

---

## 5. Stage 5 → Stage 6 Contract Definition

### 5.1 Cost Response Structure

```python
class VoyageCostResponse(BaseModel):
    """
    Structured voyage cost calculation with explicit availability.
    
    CRITICAL: All cost components follow the data honesty principle.
    Missing data is never implicitly zero.
    """
    
    # Voyage identification
    vessel_id: int
    voyage_id: Optional[int] = None
    cargo_type: str
    quantity_tonnes: float
    origin: str
    destination: str
    
    # Calculated cost components
    freight_cost: Optional[float] = None
    freight_cost_status: str  # "KNOWN" | "FORECASTED" | "ESTIMATED" | "UNAVAILABLE"
    freight_cost_source: str  # "HISTORICAL" | "ML_MODEL" | "INTERPOLATED"
    
    operational_cost: Optional[float] = None
    operational_cost_status: str  # "KNOWN" | "ADJUSTED" | "UNAVAILABLE"
    operational_cost_note: Optional[str]  # e.g., "Handysize average; vessel-specific variance ±15%"
    
    fuel_cost: Optional[float] = None
    fuel_cost_status: str  # "CALCULATED" | "ESTIMATED" | "UNAVAILABLE_FUEL_PRICE" | "UNAVAILABLE_DATA"
    fuel_cost_note: Optional[str]  # e.g., "Fuel price not available; assumed $400/tonne"
    
    port_cost: Optional[float] = None
    port_cost_status: str  # "KNOWN" | "EXTERNAL_PROVIDED" | "ESTIMATED" | "UNAVAILABLE"
    port_cost_note: Optional[str]  # e.g., "Estimated from port utilization; not actual charges"
    
    delay_cost: Optional[float] = None
    delay_cost_status: str  # "CALCULATED" | "PARTIAL_DELAY_ONLY" | "UNAVAILABLE_DEMURRAGE_RATE" | "UNAVAILABLE"
    delay_cost_note: Optional[str]  # e.g., "Delay hours calculated; demurrage rate external"
    
    congestion_surcharge: Optional[float] = None
    congestion_surcharge_status: str  # "CALCULATED" | "NOT_CALCULATED_THRESHOLD_UNDEFINED" | "UNAVAILABLE"
    congestion_surcharge_note: Optional[str]  # e.g., "Requires surcharge_factor configuration"
    
    # Intermediate values for Stage 6 calculations
    expected_delay_hours: Optional[float] = None
    port_utilization_pct: Optional[float] = None
    congestion_index: Optional[float] = None
    engine_power_kw: Optional[float] = None
    distance_nm: Optional[float] = None
    
    # Aggregated totals
    total_calculated_cost: Optional[float] = None  # Sum of all KNOWN costs
    total_estimated_cost: Optional[float] = None   # Sum including ESTIMATED
    total_landed_cost: Optional[float] = None      # Complete landed cost (None if any required component unavailable)
    
    # Cost availability matrix
    cost_availability: dict[str, bool] = {}  # e.g., {"freight": True, "fuel": False, "port": False}
    missing_components: list[str] = []  # e.g., ["fuel_price", "port_charges", "demurrage_rate"]
    
    # Metadata
    currency: str = "USD"
    timestamp: datetime
    model_version: Optional[str] = None
    data_scope: str  # "FULL_KNOWN" | "PARTIAL_ESTIMATED" | "HIGHLY_INCOMPLETE"
    
    # Explainability
    calculation_notes: list[str] = []  # Traceability of decisions
    assumptions: dict[str, Any] = {}  # Explicit assumptions made
    caveats: list[str] = []  # Important limitations
```

### 5.2 Risk Response Structure

```python
class VoyageRiskResponse(BaseModel):
    """
    Structured voyage risk assessment with explicit component availability.
    
    Risk is NOT a single score. It is a multi-dimensional assessment.
    Missing data is never implicitly low-risk.
    """
    
    # Voyage identification
    vessel_id: int
    voyage_id: Optional[int] = None
    origin: str
    destination: str
    
    # Risk components (0-100 scale)
    congestion_risk_score: Optional[float] = None  # 0-100
    congestion_risk_category: str  # "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN"
    congestion_risk_status: str  # "KNOWN" | "FORECASTED" | "UNAVAILABLE"
    
    delay_risk_hours: Optional[float] = None
    delay_risk_category: str
    delay_risk_status: str
    
    weather_risk_score: Optional[float] = None  # 0-100
    weather_risk_category: str
    weather_risk_status: str  # "HISTORICAL_PATTERN" | "FORECAST" | "UNAVAILABLE"
    weather_risk_note: Optional[str]  # e.g., "Based on historical season pattern; live forecast unavailable"
    
    market_volatility_risk_score: Optional[float] = None
    market_volatility_risk_category: str
    market_volatility_risk_status: str  # "CALCULATED" | "ESTIMATED" | "UNAVAILABLE"
    
    geopolitical_risk_score: Optional[float] = None
    geopolitical_risk_category: str
    geopolitical_risk_status: str
    geopolitical_risk_note: Optional[str]  # e.g., "GPR Index: 145 (MEDIUM); no active events on route"
    
    commodity_price_volatility_score: Optional[float] = None
    commodity_price_volatility_category: str
    commodity_price_volatility_status: str
    
    # Intermediate metrics
    port_congestion_index: Optional[float] = None  # 0-1 scale
    port_utilization_pct: Optional[float] = None
    bdi_momentum_pct: Optional[float] = None  # BDI month-over-month change
    vix_level: Optional[float] = None  # Volatility Index
    gpr_index: Optional[float] = None  # Geopolitical Risk Index
    
    # Aggregated risk
    overall_risk_score: Optional[float] = None  # 0-100 scale
    overall_risk_category: str  # "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN"
    
    # Risk availability
    risk_component_availability: dict[str, bool] = {}  # e.g., {"congestion": True, "bunker_price": False}
    unavailable_risk_factors: list[str] = []  # Risks not assessed due to missing data
    
    # Metadata
    timestamp: datetime
    forecast_horizon_days: Optional[int] = None  # How far ahead this assessment is
    model_version: Optional[str] = None
    
    # Explainability
    risk_factors_ranked: list[dict] = []  # e.g., [{"factor": "congestion", "score": 70}, ...]
    risk_catalysts: list[str] = []  # Specific risk triggers, e.g., ["Port at 95% utilization", "High BDI volatility"]
    mitigations: list[str] = []  # Possible risk mitigations (informational)
    caveats: list[str] = []  # Important limitations
```

### 5.3 Voyage Evaluation Response (Combined)

```python
class VoyageEvaluationResponse(BaseModel):
    """
    Complete voyage cost and risk evaluation for Stage 6 optimization.
    """
    
    # Identifiers
    vessel_id: int
    voyage_id: Optional[int] = None
    origin: str
    destination: str
    cargo_type: str
    quantity_tonnes: float
    arrival_date: date
    
    # Cost component
    cost: VoyageCostResponse
    
    # Risk component
    risk: VoyageRiskResponse
    
    # Metadata
    timestamp: datetime
    evaluation_status: str  # "COMPLETE" | "PARTIAL_MISSING_DATA" | "FAILED"
    
    # Stage 6 Input
    # (These fields directly feed into optimization_service.rank_options)
    feasible: bool  # From Stage 4 (assumed passed in)
    forecast: dict  # From Stage 2
    total_landed_cost: Optional[float]  # From cost.total_landed_cost
    overall_risk: Optional[float]  # From risk.overall_risk_score
    expected_delay_hours: Optional[float]  # From cost.expected_delay_hours
    
    # Rejection/Issues
    rejection_reasons: list[str] = []  # Why this option should not be ranked
```

---

## 6. Proposed Architecture

### 6.1 Directory Structure

```
backend/app/
├── cost_risk/              # NEW: Stage 5 implementation
│   ├── __init__.py
│   ├── contracts.py        # Response schemas
│   ├── cost_calculator.py  # Cost calculation logic
│   ├── risk_calculator.py  # Risk calculation logic
│   ├── data_loader.py      # Data fetching from DB/processed files
│   └── service.py          # Main orchestration
│
├── models/
│   └── voyage_evaluation.py  # NEW: Extend voyage model with cost/risk fields (optional)
│
├── schemas/
│   ├── cost_risk.py        # Response schemas (if not in contracts.py)
│   └── voyage_evaluation.py  # Combined response schema
│
└── api/routes/
    └── cost_risk.py        # NEW: API endpoints for cost/risk evaluation
```

### 6.2 Module Responsibilities

#### `cost_risk/contracts.py`
Defines all response Pydantic models:
- `CostComponent` (base model for cost components)
- `CostCalculationResponse`
- `RiskComponent` (base model for risk components)
- `RiskAssessmentResponse`
- `VoyageEvaluationResponse`

Example:
```python
class CostComponent(BaseModel):
    value: Optional[float] = None
    status: str  # "KNOWN" | "ESTIMATED" | "UNAVAILABLE"
    source: Optional[str] = None
    note: Optional[str] = None
    confidence: Optional[float] = None

class CostCalculationResponse(BaseModel):
    vessel_id: int
    freight_cost: CostComponent
    operational_cost: CostComponent
    fuel_cost: CostComponent
    port_cost: CostComponent
    delay_cost: CostComponent
    # ... other components
    total_landed_cost: Optional[float]
    missing_components: list[str]
    # ... metadata
```

#### `cost_risk/data_loader.py`
Fetches required data:
- Query Freight model for forecast_rate
- Query Vessel model for operational characteristics
- Query Port model for congestion metrics
- Load processed CSV files (vessel_performance, freight_rates, port_congestion, etc.)
- Query Prediction model for Stage 2/Stage 3 outputs

```python
def get_freight_forecast(voyage_id: int, db: Session) -> dict:
    """Query Stage 2 forecast."""
    
def get_congestion_data(port_id: int, db: Session) -> dict:
    """Query Stage 3 congestion prediction."""
    
def get_vessel_operational_baseline(ship_type: str) -> dict:
    """Load from vessel_performance_processed.csv."""
    
def get_freight_rate_baseline(vessel_class: str, date: date) -> dict:
    """Load from freight_rates.csv."""
    
def get_port_congestion_baseline(port_name: str, date: date) -> dict:
    """Load from port_congestion_processed.csv."""
```

#### `cost_risk/cost_calculator.py`
Calculates cost components:

```python
def calculate_freight_cost(
    quantity_tonnes: float,
    forecast: Optional[dict],  # Stage 2 output
    vessel_class: str,
    date: date,
) -> CostComponent:
    """
    Calculate or forecast freight cost.
    Returns CostComponent with status and source.
    """
    # If forecast available and confidence high: return FORECASTED
    # Else if historical rate available: return KNOWN
    # Else: return UNAVAILABLE

def calculate_operational_cost(
    quantity_tonnes: float,
    vessel_class: str,
    route_type: str,  # e.g., "transoceanic"
    maintenance_status: str,  # From vessel model
    season: int,  # Derived from date
) -> CostComponent:
    """
    Calculate operational cost from historical patterns.
    Based on vessel_performance_processed.csv.
    """

def calculate_fuel_cost(
    distance_nm: float,
    engine_power_kw: float,
    speed_knots: float,
    bunker_price_per_tonne: Optional[float] = None,
) -> CostComponent:
    """
    Calculate fuel cost.
    If bunker_price provided: return CALCULATED
    Else: return UNAVAILABLE_FUEL_PRICE with intermediate values
    """

def calculate_port_cost(
    port_id: int,
    db: Session,
    port_handling_rate: Optional[float] = None,  # External parameter
) -> CostComponent:
    """
    Calculate or accept port cost.
    If external rate provided: return KNOWN
    Else: return UNAVAILABLE
    """

def calculate_delay_cost(
    delay_hours: float,
    demurrage_rate_per_day: Optional[float] = None,
) -> CostComponent:
    """
    Calculate delay cost (demurrage).
    If demurrage_rate provided: return CALCULATED
    Else: return UNAVAILABLE_DEMURRAGE_RATE with delay_hours
    """

def aggregate_cost(
    components: dict[str, CostComponent],
) -> CostCalculationResponse:
    """
    Aggregate all components into total_landed_cost.
    Only include components with KNOWN status.
    Return None if any required component is missing.
    """
```

#### `cost_risk/risk_calculator.py`
Calculates risk components:

```python
def calculate_congestion_risk(
    port_id: int,
    db: Session,
    date: date,
) -> RiskComponent:
    """
    Calculate congestion risk from port data or Stage 3 forecast.
    """

def calculate_delay_risk(
    congestion_data: dict,
) -> RiskComponent:
    """
    Derive delay risk from congestion data.
    """

def calculate_weather_risk(
    route: str,
    destination: str,
    date: date,
    forecast_data: Optional[dict] = None,
) -> RiskComponent:
    """
    Assess weather risk based on historical patterns or forecast.
    """

def calculate_market_volatility_risk(
    date: date,
) -> RiskComponent:
    """
    Calculate from BDI momentum, commodity price volatility, VIX.
    """

def calculate_geopolitical_risk(
    route: tuple[str, str],  # (origin, destination)
    date: date,
) -> RiskComponent:
    """
    Calculate from GPR index and event data.
    """

def calculate_commodity_price_volatility(
    commodity: str,
    lookback_days: int = 90,
) -> RiskComponent:
    """
    Calculate price volatility from commodity_prices_processed.csv.
    """

def aggregate_risk(
    components: dict[str, RiskComponent],
) -> RiskAssessmentResponse:
    """
    Aggregate all risk components into overall_risk_score.
    Use only available components (weighted average).
    Document unavailable factors.
    """
```

#### `cost_risk/service.py`
Main orchestration:

```python
def evaluate_voyage(
    voyage_id: int,
    vessel_id: int,
    port_id: int,
    db: Session,
    # Optional external parameters for unavailable data:
    bunker_price_per_tonne: Optional[float] = None,
    port_handling_rate_per_tonne: Optional[float] = None,
    demurrage_rate_per_day: Optional[float] = None,
    surcharge_factor: Optional[float] = None,  # For congestion surcharge
) -> VoyageEvaluationResponse:
    """
    Complete voyage evaluation.
    1. Load voyage, vessel, port data
    2. Fetch Stage 2 forecast
    3. Fetch Stage 3 congestion prediction
    4. Fetch Stage 4 feasibility result (if exists)
    5. Calculate all cost components
    6. Calculate all risk components
    7. Aggregate into response
    8. Return VoyageEvaluationResponse
    """
    
    # Workflow:
    cost = cost_calculator.aggregate_cost(...)
    risk = risk_calculator.aggregate_risk(...)
    
    return VoyageEvaluationResponse(
        vessel_id=vessel_id,
        voyage_id=voyage_id,
        cost=cost,
        risk=risk,
        total_landed_cost=cost.total_landed_cost,
        overall_risk=risk.overall_risk_score,
        # ... etc
    )

def evaluate_candidates(
    voyage_id: int,
    candidate_vessels: list[int],
    candidate_ports: list[int],
    db: Session,
) -> list[VoyageEvaluationResponse]:
    """
    Evaluate all candidate vessel-port combinations.
    Returns list for Stage 6 ranking.
    """
```

#### `api/routes/cost_risk.py`
API endpoints:

```python
router = APIRouter(prefix="/cost-risk", tags=["Cost & Risk"])

@router.post("/evaluate", response_model=VoyageEvaluationResponse)
def evaluate_voyage(
    request: VoyageEvaluationRequest,  # Contains voyage_id, vessel_id, port_id
    db: Session = Depends(get_db),
):
    """Evaluate a single voyage's cost and risk."""
    return cost_risk_service.evaluate_voyage(
        voyage_id=request.voyage_id,
        vessel_id=request.vessel_id,
        port_id=request.port_id,
        db=db,
        bunker_price_per_tonne=request.bunker_price_per_tonne,
        # ... other optional parameters
    )

@router.post("/evaluate-candidates", response_model=list[VoyageEvaluationResponse])
def evaluate_candidates(
    request: VoyageEvaluationBatchRequest,
    db: Session = Depends(get_db),
):
    """Evaluate multiple vessel-port combinations for a voyage."""
    return cost_risk_service.evaluate_candidates(
        voyage_id=request.voyage_id,
        candidate_vessels=request.candidate_vessels,
        candidate_ports=request.candidate_ports,
        db=db,
    )
```

---

## 7. Implementation Sequencing

### Phase 1: Contracts & Data Loading (Week 1)
1. Define `cost_risk/contracts.py` with full response schemas
2. Implement `cost_risk/data_loader.py` to fetch all required data
3. Create unit tests for data loading
4. Validation: Ensure all data sources are correctly queried

### Phase 2: Cost Calculator (Week 2)
1. Implement freight cost calculation (from forecast service)
2. Implement operational cost calculation (from vessel_performance baseline)
3. Implement fuel cost calculation (flagged as unavailable)
4. Implement port cost calculation (flagged as unavailable)
5. Implement delay cost calculation (with external demurrage_rate parameter)
6. Implement aggregation logic
7. Create comprehensive unit tests

### Phase 3: Risk Calculator (Week 2-3)
1. Implement congestion risk calculation
2. Implement delay risk calculation
3. Implement weather risk calculation (historical patterns)
4. Implement market volatility risk calculation
5. Implement geopolitical risk calculation
6. Implement commodity price volatility calculation
7. Create comprehensive unit tests

### Phase 4: Service Orchestration (Week 3)
1. Implement `cost_risk/service.py` orchestration
2. Integrate with Stage 2 forecast service
3. Integrate with Stage 3 congestion service (when available)
4. Implement batch evaluation for candidates
5. Create integration tests

### Phase 5: API Routes (Week 3)
1. Implement `api/routes/cost_risk.py` endpoints
2. Connect to service layer
3. Create endpoint tests

### Phase 6: Documentation & Testing (Week 4)
1. Write comprehensive test suite (see Section 8)
2. Create `docs/stage5_cost_risk.md`
3. Regression testing against Stage 2 & 3
4. Performance testing

---

## 8. Comprehensive Testing Strategy

### 8.1 Test Modules

#### `tests/test_cost_risk_contracts.py`
**Purpose:** Validate all response schemas

```python
# Test contract schemas
def test_cost_component_with_known_status():
    """CostComponent correctly represents known cost."""
    
def test_cost_component_with_unavailable_status():
    """CostComponent correctly represents unavailable cost."""
    
def test_cost_calculation_response_serialization():
    """Response can be serialized to JSON."""
    
def test_risk_component_with_all_fields():
    """RiskComponent handles all fields correctly."""
    
def test_voyage_evaluation_response_complete():
    """Complete response with all sub-components."""
```

#### `tests/test_cost_calculator.py`
**Purpose:** Unit test cost calculation logic

```python
# Freight cost tests
def test_freight_cost_from_forecast_high_confidence():
    """Freight cost calculated from ML forecast (confidence > threshold)."""
    
def test_freight_cost_from_forecast_low_confidence():
    """Freight cost status UNAVAILABLE if confidence too low."""
    
def test_freight_cost_from_historical_rate():
    """Fallback to historical rate if forecast unavailable."""
    
def test_freight_cost_unavailable_no_data():
    """Freight cost unavailable when no data source exists."""

# Operational cost tests
def test_operational_cost_by_vessel_class():
    """Operational cost calculated from vessel class baseline."""
    
def test_operational_cost_adjusted_for_maintenance():
    """Operational cost adjusted by maintenance status."""
    
def test_operational_cost_adjusted_for_season():
    """Operational cost adjusted by seasonal factor."""
    
def test_operational_cost_by_route_type():
    """Operational cost varies by route type (transoceanic > long-haul)."""

# Fuel cost tests
def test_fuel_cost_unavailable_no_bunker_price():
    """Fuel cost flagged UNAVAILABLE_FUEL_PRICE when no bunker data."""
    
def test_fuel_cost_intermediate_values_provided():
    """Even if unavailable, fuel cost returns engine_power, distance, speed."""
    
def test_fuel_cost_calculated_with_external_price():
    """Fuel cost calculated when bunker_price provided externally."""

# Port cost tests
def test_port_cost_unavailable_by_default():
    """Port cost unavailable when no external rate provided."""
    
def test_port_cost_known_with_external_rate():
    """Port cost calculated when external rate provided."""

# Delay cost tests
def test_delay_cost_unavailable_no_demurrage_rate():
    """Delay cost flagged UNAVAILABLE_DEMURRAGE_RATE when no demurrage data."""
    
def test_delay_cost_partial_delay_only():
    """Delay hours calculated even if demurrage_rate unavailable."""
    
def test_delay_cost_calculated_with_external_demurrage():
    """Delay cost calculated when demurrage_rate provided."""

# Aggregation tests
def test_total_landed_cost_all_known():
    """Total cost calculated when all components KNOWN."""
    
def test_total_landed_cost_none_if_required_missing():
    """Total cost is None if any required component missing."""
    
def test_missing_components_list_populated():
    """List of missing components correctly identified."""
    
def test_cost_availability_matrix():
    """Cost availability matrix correctly reflects component status."""

# Boundary tests
def test_zero_quantity_tonnes():
    """Handles zero quantity correctly (cost = 0 or error?)."""
    
def test_negative_cost_values():
    """Rejects negative cost values as invalid."""
    
def test_extreme_high_cost_values():
    """Handles extreme (but valid) cost values."""
```

#### `tests/test_risk_calculator.py`
**Purpose:** Unit test risk calculation logic

```python
# Congestion risk tests
def test_congestion_risk_low():
    """Congestion index 0.1 → LOW risk."""
    
def test_congestion_risk_medium():
    """Congestion index 0.5 → MEDIUM risk."""
    
def test_congestion_risk_high():
    """Congestion index 0.9 → HIGH risk."""
    
def test_congestion_risk_unavailable():
    """Congestion risk UNAVAILABLE if no port data."""

# Delay risk tests
def test_delay_risk_low():
    """Delay < 48 hours → LOW risk."""
    
def test_delay_risk_medium():
    """Delay 48-144 hours → MEDIUM risk."""
    
def test_delay_risk_high():
    """Delay > 144 hours → HIGH risk."""
    
def test_delay_risk_from_congestion():
    """Delay risk correctly derived from congestion metrics."""

# Weather risk tests
def test_weather_risk_calm():
    """Calm conditions → LOW risk."""
    
def test_weather_risk_moderate():
    """Moderate conditions → MEDIUM risk."""
    
def test_weather_risk_rough():
    """Rough conditions → HIGH risk."""
    
def test_weather_risk_seasonal_adjustment():
    """Weather risk adjusted by season (e.g., monsoon)."""
    
def test_weather_risk_route_dependency():
    """Weather risk higher for transoceanic vs short-haul."""

# Market volatility tests
def test_market_volatility_low():
    """Low BDI change + low commodity volatility → LOW risk."""
    
def test_market_volatility_high():
    """High volatility in multiple indicators → HIGH risk."""
    
def test_market_volatility_partial_data():
    """Market volatility calculated from available indicators."""

# Geopolitical risk tests
def test_geopolitical_risk_low():
    """GPR index < 100 → LOW risk."""
    
def test_geopolitical_risk_medium():
    """GPR index 100-150 → MEDIUM risk."""
    
def test_geopolitical_risk_high():
    """GPR index > 150 → HIGH risk."""
    
def test_geopolitical_risk_event_modifier():
    """Active events increase risk score."""

# Commodity price volatility tests
def test_commodity_price_volatility_stable():
    """Stable prices (volatility < 5%) → LOW risk."""
    
def test_commodity_price_volatility_moderate():
    """Moderate volatility (5-15%) → MEDIUM risk."""
    
def test_commodity_price_volatility_high():
    """High volatility (> 15%) → HIGH risk."""

# Aggregation tests
def test_overall_risk_score_weighted_average():
    """Overall risk is weighted average of components."""
    
def test_overall_risk_excludes_unavailable():
    """Unavailable components not included in average."""
    
def test_overall_risk_none_if_all_unavailable():
    """Overall risk is None if all components unavailable."""
    
def test_unavailable_risk_factors_list():
    """List of unavailable risk factors correctly identified."""

# Boundary tests
def test_risk_score_0_to_100_range():
    """All risk scores normalized to 0-100 range."""
    
def test_invalid_risk_negative():
    """Rejects negative risk scores."""
    
def test_invalid_risk_exceeds_100():
    """Clips or rejects risk scores > 100."""
```

#### `tests/test_cost_risk_service.py`
**Purpose:** Integration tests for full workflow

```python
# Complete voyage evaluation tests
def test_evaluate_voyage_complete_data():
    """Full voyage evaluation with all data available."""
    
def test_evaluate_voyage_partial_data():
    """Voyage evaluation with some missing components."""
    
def test_evaluate_voyage_missing_critical_data():
    """Voyage evaluation returns partial result for critical missing data."""
    
def test_evaluate_voyage_integrates_stage2_forecast():
    """Freight forecast from Stage 2 correctly integrated."""
    
def test_evaluate_voyage_integrates_stage3_congestion():
    """Congestion prediction from Stage 3 correctly integrated (when available)."""

# Batch evaluation tests
def test_evaluate_candidates_multiple_vessels():
    """Batch evaluation across multiple vessel candidates."""
    
def test_evaluate_candidates_multiple_ports():
    """Batch evaluation across multiple port candidates."""
    
def test_evaluate_candidates_results_consistent():
    """Evaluating individually vs batch produces same results."""
    
def test_evaluate_candidates_ranking_order():
    """Candidates correctly rankable by cost/risk."""

# External parameter handling tests
def test_external_bunker_price_supplied():
    """Fuel cost calculated when external bunker price provided."""
    
def test_external_port_rate_supplied():
    """Port cost calculated when external rate provided."""
    
def test_external_demurrage_rate_supplied():
    """Delay cost calculated when external demurrage provided."""
    
def test_external_surcharge_factor_supplied():
    """Congestion surcharge calculated when factor provided."""

# Stage 6 compatibility tests
def test_response_compatible_with_rank_options():
    """Response structure compatible with optimization_service.rank_options()."""
    
def test_total_landed_cost_field_matches_optimization():
    """total_landed_cost field correctly passed to Stage 6."""
    
def test_overall_risk_field_matches_optimization():
    """overall_risk field correctly passed to Stage 6."""
    
def test_expected_delay_hours_field_matches_optimization():
    """expected_delay_hours field correctly passed to Stage 6."""

# Error handling tests
def test_invalid_voyage_id():
    """Gracefully handles invalid voyage_id."""
    
def test_invalid_vessel_id():
    """Gracefully handles invalid vessel_id."""
    
def test_invalid_port_id():
    """Gracefully handles invalid port_id."""
    
def test_missing_required_parameters():
    """Validation error for missing required inputs."""
```

#### `tests/test_stage5_regression.py`
**Purpose:** Regression and data honesty tests

```python
# Data honesty tests
def test_no_fabricated_fuel_cost():
    """Fuel cost never fabricated; always flagged unavailable if data missing."""
    
def test_no_fabricated_port_charges():
    """Port charges never fabricated; always flagged unavailable if data missing."""
    
def test_no_fabricated_demurrage_rates():
    """Demurrage rates never fabricated; always flagged unavailable if data missing."""
    
def test_no_implicit_zero_for_missing_data():
    """Missing data never implicitly treated as zero."""
    
def test_no_implicit_low_risk_for_missing_data():
    """Missing risk data never implicitly treated as low-risk."""

# Determinism tests
def test_same_inputs_produce_same_output():
    """Identical inputs produce identical outputs (deterministic)."""
    
def test_different_execution_order_same_result():
    """Result independent of component calculation order."""
    
def test_concurrent_evaluations_consistent():
    """Concurrent evaluations of same voyage produce consistent results."""

# Traceability tests
def test_calculation_notes_include_all_decisions():
    """calculation_notes field includes all significant decisions."""
    
def test_assumptions_field_documented():
    """All assumptions explicitly documented in assumptions dict."""
    
def test_caveats_field_populated():
    """Important limitations included in caveats list."""
    
def test_source_tracking_for_each_component():
    """Each component includes source tracking."""

# Stage 2 compatibility tests
def test_accepts_forecast_response_from_stage2():
    """Correctly accepts ForecastResponse from Stage 2."""
    
def test_handles_unavailable_forecast():
    """Correctly handles forecast with data_status=UNAVAILABLE."""
    
def test_forecast_confidence_threshold():
    """Respects confidence threshold for forecast adoption."""

# Stage 3 compatibility tests (when available)
def test_accepts_congestion_prediction_from_stage3():
    """Correctly accepts congestion output from Stage 3."""
    
def test_handles_unavailable_congestion():
    """Correctly handles congestion with data_status=UNAVAILABLE."""

# Stage 6 compatibility tests
def test_output_structure_matches_recommendation_schema():
    """Response structure compatible with recommendation_service.RecommendationResponse."""
    
def test_missing_components_dont_break_stage6():
    """Stage 6 can handle responses with missing components."""
    
def test_none_values_handled_by_stage6_ranking():
    """Stage 6 rank_options() correctly handles None values in cost/risk."""

# API endpoint tests
def test_api_evaluate_endpoint():
    """POST /cost-risk/evaluate returns correct response."""
    
def test_api_evaluate_candidates_endpoint():
    """POST /cost-risk/evaluate-candidates returns list of responses."""
    
def test_api_error_handling():
    """API returns appropriate error status codes for invalid input."""
```

### 8.2 Test Data

#### Fixture: Complete Voyage
```python
@pytest.fixture
def complete_voyage():
    """Voyage with all required data available."""
    return {
        "voyage_id": 1,
        "vessel_id": 10,
        "port_id": 100,
        "cargo_type": "coal",
        "quantity_tonnes": 75000.0,
        "origin": "Australia",
        "destination": "Visakhapatnam",
        "arrival_date": date(2026, 9, 20),
        "forecast": {  # From Stage 2
            "forecast_rate": 45.50,
            "confidence": 0.85,
            "data_status": "KNOWN",
        },
        "vessel": {
            "name": "MV XYZ",
            "dwt": 80000,
            "loa_m": 225,
            "draft_m": 12.5,
            "cargo_types": "Dry Bulk",
        },
        "port": {
            "name": "Visakhapatnam",
            "utilization_percent": 72,
            "avg_wait_days": 2.5,
            "berth_delay_hrs": 18,
        },
    }
```

#### Fixture: Incomplete Voyage
```python
@pytest.fixture
def incomplete_voyage():
    """Voyage with some missing components."""
    # Same as complete_voyage but with bunker_price=None, demurrage_rate=None
```

### 8.3 Test Coverage Goals

- **Cost Calculator:** 95%+ coverage
- **Risk Calculator:** 95%+ coverage
- **Service:** 90%+ coverage
- **Overall:** 92%+ coverage

### 8.4 Performance Tests

```python
def test_single_voyage_evaluation_latency():
    """Single voyage evaluation completes < 500ms."""
    
def test_batch_evaluation_100_candidates():
    """Batch evaluation of 100 candidates completes < 5s."""
    
def test_concurrent_evaluations_throughput():
    """System handles 10 concurrent evaluations."""
```

---

## 9. Data Honesty Checklist

### 9.1 Cost Components

- [ ] Freight cost: Never assumed zero; status tracked
- [ ] Operational cost: Derived from actual data; vessel-class dependency noted
- [ ] Fuel cost: Explicitly UNAVAILABLE when bunker price missing
- [ ] Port cost: Explicitly UNAVAILABLE unless externally provided
- [ ] Delay cost: Delay hours calculated; demurrage rate required separately
- [ ] Congestion surcharge: Explicitly NOT calculated until surcharge_factor defined
- [ ] Insurance cost: NOT calculated (no data)
- [ ] Other costs: NOT calculated (no data)

### 9.2 Risk Components

- [ ] Congestion risk: From actual data; None when data unavailable
- [ ] Delay risk: Derived from congestion data
- [ ] Weather risk: Historical patterns only; forecast marked as unavailable
- [ ] Market volatility: From actual BDI, commodity prices, VIX
- [ ] Geopolitical risk: From GPR index; event-specific only
- [ ] Commodity price volatility: From actual price data
- [ ] Bunker price risk: NOT calculated (no bunker data)
- [ ] Currency risk: NOT calculated (not in data)
- [ ] Vessel-specific risk: Limited to maintenance status
- [ ] Regulatory risk: NOT calculated (not in data)

### 9.3 Missing Data Handling

- [ ] No implicit zero for missing costs
- [ ] No implicit low-risk for missing risks
- [ ] All unavailable components explicitly listed
- [ ] status field distinguishes KNOWN, ESTIMATED, UNAVAILABLE, etc.
- [ ] Confidence/credibility tracked for estimated values
- [ ] Assumptions documented
- [ ] Caveats listed for Stage 6 awareness

---

## 10. Configuration & Thresholds

### 10.1 Configurable Parameters

**Risk Thresholds (can be overridden at system startup):**
```python
RISK_THRESHOLDS = {
    "congestion": {"low": 0.33, "high": 0.66},
    "delay_hours": {"low": 48, "high": 144},
    "weather": {"categories": ["calm", "moderate", "rough"]},
    "market_volatility": {"low": 30, "high": 60},
    "geopolitical": {"low": 100, "high": 150},
    "commodity_volatility": {"low": 0.05, "high": 0.15},
}
```

**Cost Surcharges:**
```python
COST_MODIFIERS = {
    "congestion_surcharge_factor": 0.05,  # 5% max surcharge per point
    "seasonal_impact_multiplier": {"factor_by_month": {...}},
    "maintenance_cost_multiplier": {
        "good": 1.0,
        "fair": 1.15,
        "critical": 1.35,
    },
}
```

**External Cost Parameters (to be supplied by Stage 6 or config):**
```python
EXTERNAL_PARAMETERS = {
    "bunker_price_per_tonne": None,  # USD/tonne (must supply or mark unavailable)
    "port_handling_rate_per_tonne": None,  # USD/tonne (must supply or mark unavailable)
    "demurrage_rate_per_day": None,  # USD/day (must supply or mark unavailable)
    "surcharge_factor": None,  # For congestion surcharge
}
```

---

## 11. Documentation Deliverables

### 11.1 `docs/stage5_cost_risk.md`

Comprehensive documentation including:

1. **Overview**
   - Purpose and scope
   - Position in decision pipeline
   - Key design principles

2. **Cost Calculation Methodology**
   - Each cost component: formula, data source, availability
   - Assumptions and limitations
   - Thresholds and configurations
   - Examples: sample calculations

3. **Risk Assessment Methodology**
   - Each risk component: calculation, data source, availability
   - Risk scoring: thresholds and categories
   - Unavailable risk factors
   - Examples: risk scenarios

4. **Response Schemas**
   - JSON structure for cost response
   - JSON structure for risk response
   - Field definitions
   - Status values and meanings

5. **Stage 5 → Stage 6 Contract**
   - Required fields
   - Optional fields
   - Data formats
   - Null handling

6. **API Reference**
   - Endpoints: POST /cost-risk/evaluate, POST /cost-risk/evaluate-candidates
   - Request/response examples
   - Error codes

7. **Configuration Guide**
   - Overridable thresholds
   - External parameters (bunker price, etc.)
   - Environment variables

8. **Data Honesty Commitment**
   - Policy on missing data
   - No fabrication rule
   - Component availability tracking
   - Caveat documentation

9. **Limitations & Future Work**
   - Why certain components unavailable
   - Data required for future enhancements
   - Roadmap for data integration

10. **Examples**
    - Example cost calculation walkthrough
    - Example risk assessment walkthrough
    - Example batch evaluation output

---

## 12. Key Design Principles

### 12.1 Data Honesty
**Principle:** Never fabricate numerical data. Always state unavailability explicitly.

**Implementation:**
- Every cost/risk component includes a `status` field
- `status ∈ {"KNOWN", "FORECASTED", "ESTIMATED", "UNAVAILABLE", "UNAVAILABLE_<REASON>"}`
- Missing data never implicitly becomes zero or low-risk
- Missing components listed in response
- Assumptions documented

### 12.2 Transparency
**Principle:** All calculations are deterministic and traceable.

**Implementation:**
- Source tracking for each component
- Calculation notes documenting decisions
- Intermediate values exposed (for Stage 6 to use)
- Confidence/credibility indicators
- No "magic" adjustments without documentation

### 12.3 Determinism
**Principle:** Identical inputs produce identical outputs.

**Implementation:**
- No randomization
- No floating-point approximations without bounds
- No external state (thread-safe)
- Results independent of calculation order

### 12.4 Delegation to Stage 6
**Principle:** Stage 5 calculates; Stage 6 decides.

**Implementation:**
- Stage 5 does NOT rank options
- Stage 5 does NOT select thresholds unilaterally
- Stage 5 accepts external parameters (bunker price, demurrage rate, surcharge factor)
- Stage 5 provides all available information for Stage 6 to make decisions
- Stage 5 does NOT optimize or perform MILP/CP-SAT

---

## 13. Risk & Mitigation

### 13.1 Identified Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Missing bunker price data | Cannot calculate fuel cost | Explicitly flag as unavailable; provide engine power/distance/speed for Stage 6 |
| Port charges not in dataset | Cannot calculate port cost | Accept external port rate parameter; document unavailability |
| No Stage 4 feasibility output yet | Stage 5 assumes feasible=True | Implement feasibility check later; Stage 5 ready for integration |
| No future weather forecast | Weather risk limited to historical patterns | Document forecast requirement; provide mechanism for external forecast data |
| Indian port data not available | Cannot assess India-specific congestion | Use global port data as proxy; clearly document limitation |
| Demurrage rates vary by charter party | Cannot assume universal rate | Accept demurrage_rate as external parameter |
| Seasonal variations complex | Simplified seasonal adjustment | Use historical season factors; document limitations |

### 13.2 Validation & Safety

- Comprehensive test suite (92%+ coverage)
- Regression tests against Stages 2–3
- API contract validation
- JSON schema validation for all responses
- Null/None handling for all inputs
- Boundary value testing
- Concurrency testing

---

## 14. Success Criteria

### 14.1 Functional Criteria

- ✅ All cost components calculated from actual available data
- ✅ All cost components with explicit availability status
- ✅ Total landed cost only returned when all required components available
- ✅ All risk components calculated from actual available data
- ✅ All risk components with explicit availability status
- ✅ Overall risk score only calculated from available components
- ✅ No fabricated values for any cost or risk
- ✅ External parameters (bunker price, demurrage rate) accepted and used
- ✅ Full traceability: source, assumptions, caveats documented

### 14.2 Quality Criteria

- ✅ 92%+ test coverage
- ✅ All endpoints pass integration tests
- ✅ Stage 2 forecast correctly integrated
- ✅ Stage 3 congestion correctly integrated (when available)
- ✅ Output compatible with Stage 6 ranking logic
- ✅ Deterministic results (same inputs → same outputs)
- ✅ Latency < 500ms per voyage
- ✅ Handles concurrent requests

### 14.3 Documentation Criteria

- ✅ Comprehensive `docs/stage5_cost_risk.md`
- ✅ Inline code documentation
- ✅ Response schema examples
- ✅ Configuration guide
- ✅ Data honesty checklist
- ✅ API reference

---

## 15. Summary

**Stage 5 is a deterministic, transparent cost and risk calculation engine that:**

1. **Consumes verified data** from Stages 1–4 (or simulated Stage 4)
2. **Calculates cost components** using actual available data
3. **Calculates risk components** using actual available data
4. **Explicitly marks unavailable components** without fabrication
5. **Provides full traceability** (source, assumptions, caveats)
6. **Produces structured output** compatible with Stage 6 ranking
7. **Accepts external parameters** for currently-unavailable cost inputs
8. **Never assumes zero** for missing data
9. **Never assumes low-risk** for missing risk factors
10. **Delegates decision-making** to Stage 6 (optimization) and project stakeholders

**Next Steps:**
- Inspect Stage 4 (Feasibility) requirements if they become available
- Begin Phase 1 implementation (contracts & data loading)
- Parallel: Confirm external parameter sources with project stakeholders (bunker price, port charges, demurrage rates)

---

**Plan Version:** 1.0  
**Date:** 2026-09-07  
**Author:** FreightWise Planning Team  
**Status:** Ready for Review
