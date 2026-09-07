# FreightWise Stage 6 — Integrated Freight, Charter & Cargo Procurement Optimization Engine

## 1. Overview
Stage 6 represents the central numerical decision and optimization engine of the FreightWise platform. It consumes forecasts, operational predictions, port feasibility assessments, and cost/risk metrics from Stages 2–5 to generate mathematically optimal vessel chartering, cargo procurement, route allocation, and market entry timing decisions.

---

## 2. Decision Pipeline & Candidate Flow

```
Candidate Route Generation (Origins × East Coast Ports × Commodities × Periods)
                               │
                               ▼
                Stage 4 Feasibility Filtering
      ┌────────────────────────┼────────────────────────┐
      │                        │                        │
      ▼                        ▼                        ▼
  FEASIBLE               INFEASIBLE              DATA_UNAVAILABLE
 (Admitted to           (Rejected)              (Excluded from Executable Plan,
 Primary Executable Pool)                         Reported Separately for Review)
      │
      ▼
 Enrichment Adapters (Stage 2 Freight, Stage 3 Delay, Stage 5 Cost/Risk)
      │
      ▼
 CP-SAT Solver (4-Priority Lexicographic / USD-Normalized Cost Minimization)
      │
      ▼
 Optimal Executable Plan + Solution Pool Alternatives + Multi-Scenario Evaluation
```

---

## 3. Mandatory Scope Enforcements & Data Honesty Rules

1. **Default Executable Plans**:
   - Only candidates with Stage 4 status `FEASIBLE` are admitted to default executable plans.
   - Candidates returning `DATA_UNAVAILABLE` are excluded from executable plans and reported separately in `unavailable_candidates[]`.
2. **Indian Port Congestion Scope**:
   - `PortCongestionService` throws `IndiaPortDataAbsentError` for Indian ports.
   - Stage 6 catches this and explicitly labels the output as `GLOBAL_CONGESTION_PROXY`. It is **never** presented as Indian-port-specific congestion.
3. **Vessel Archetype Labeling**:
   - Since physical ship IDs (`vessel_id`), DWT, and dimensions are absent from the dataset, Stage 6 strictly optimizes and labels decisions as **Vessel Charter Archetypes / Slots** (e.g. `Bulk Carrier Handysize Archetype Slot #1`). Zero fake ship names or IMO numbers are generated.
4. **No Data Fabrication**:
   - Stage 6 never fabricates vessel availability calendars, port channel depths, port charges, fuel prices, or procurement prices.

---

## 4. Reconciled Hierarchical Objective Formulation

Stage 6 implements a **4-Priority Lexicographic Objective**:
- **Priority 1: Hard Feasibility**: Zero selection of Stage 4 infeasible candidates.
- **Priority 2: Demand Fulfillment**: Minimize commodity demand shortage $\sum \max(0, D_c - \sum q)$.
- **Priority 3: Economic Delivered Cost**: Minimize $\sum (\text{VoyageCost} + \text{FreightRate}_t \times \text{VoyageDays}) \cdot x$.
- **Priority 4: Operational Risk & Delay Penalties**: Minimize turnaround delay, delay risk score, commercial risk score, and global congestion proxy index.

In single-pass mode, all penalty terms are normalized into **USD Currency Units** using configurable business parameters ($w_{\text{delay}}$, $w_{\text{risk}}$, $w_{\text{cong\_proxy}}$, $w_{\text{shortage}}$).

---

## 5. Public API Usage

```python
from src.optimization import OptimizationService, OptimizationRequest, DemandTarget

service = OptimizationService()

request = OptimizationRequest(
    horizon_periods=3,
    planning_start_date="2024-10-01",
    demand_targets=[
        DemandTarget(commodity="Coal", target_quantity_tons=60000)
    ],
    max_charters_per_period=5
)

result = service.optimize(request)

print(f"Status: {result.solver_status}")
if result.primary_executable_plan:
    print(f"Total Cost: ${result.primary_executable_plan.total_cost_usd:,.2f}")
    print(f"Procured Cargo: {result.primary_executable_plan.total_cargo_tons:,} tons")
    for alloc in result.primary_executable_plan.allocations:
        print(f"  - Period {alloc.period}: {alloc.origin} -> {alloc.destination_port} ({alloc.cargo_quantity_tons} tons, Rate: ${alloc.forecast_freight_usd_day}/day)")

print(f"Unavailable Candidates Needing Manual Review: {len(result.unavailable_candidates)}")
```
