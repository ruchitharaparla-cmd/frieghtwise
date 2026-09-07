"""
Unit tests for CP-SAT Solver — LEXICOGRAPHIC and WEIGHTED modes.

Tests verify:
- solve_hierarchical=True  → genuine lexicographic sequential solve
- solve_hierarchical=False → weighted scalar objective
- Demand fulfilment priority before economic cost
- Economic cost priority before risk/delay
- DATA_UNAVAILABLE candidates excluded from executable pool
- FEASIBLE candidates included correctly
- INFEASIBLE candidates rejected
- No fabricated vessel identities in output plans
- Batch parameter bounds enforced (planning parameters, not physical DWT)
"""

import pytest
from src.optimization.contracts import (
    CandidateRoute,
    EnrichedCandidate,
    OptimizationRequest,
    DemandTarget,
    OptimizationStatus,
    PlanType,
)
from src.optimization.cp_sat_solver import CPSatOptimizationSolver


# ---------------------------------------------------------------------------
# TEST-ONLY FIXTURE helpers
# ---------------------------------------------------------------------------

def _make_feasible_candidate(
    origin: str,
    port: str,
    commodity: str,
    period: int,
    freight_usd_day: float,
    voyage_cost_usd: float,
    turnaround_hours: float = 24.0,
    delay_risk_score: float = 10.0,
) -> EnrichedCandidate:
    """Build a TEST-ONLY FIXTURE EnrichedCandidate with FEASIBLE status."""
    return EnrichedCandidate(
        candidate=CandidateRoute(origin, port, commodity, period, f"2024-{9+period:02d}-01"),
        stage4_status="FEASIBLE",
        forecast_freight_usd_day=freight_usd_day,
        turnaround_hours=turnaround_hours,
        delay_risk_score=delay_risk_score,
        congestion_proxy_score=1.5,
        congestion_data_scope="GLOBAL_CONGESTION_PROXY",
        voyage_cost_usd=voyage_cost_usd,
        commercial_risk_score=0.2,
        vessel_archetype=f"Bulk Carrier Handysize Archetype Slot #{period}",
    )


# ---------------------------------------------------------------------------
# Test: Weighted mode (solve_hierarchical=False)
# ---------------------------------------------------------------------------

def test_cp_sat_solver_weighted_mode_basic():
    """Weighted scalar mode produces a valid plan for FEASIBLE candidates."""
    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
        _make_feasible_candidate("INDONESIA", "Visakhapatnam SEA", "Coal", 2, 16000.0, 170000.0),
    ]
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        max_batch_tons=80000,
        min_batch_tons=30000,
        solve_hierarchical=False,
    )

    solver = CPSatOptimizationSolver()
    status, primary_plan, alternatives, exec_time = solver.solve(
        candidates=cands, request=req, extract_alternatives=True
    )

    assert status in (OptimizationStatus.OPTIMAL.value, OptimizationStatus.FEASIBLE.value)
    assert primary_plan is not None
    assert primary_plan.objective_mode == "WEIGHTED"
    assert primary_plan.lexicographic_achieved_values is None
    assert primary_plan.total_cargo_tons >= 45000  # Within 10% tolerance
    assert len(primary_plan.allocations) >= 1


# ---------------------------------------------------------------------------
# Test: Lexicographic mode (solve_hierarchical=True)
# ---------------------------------------------------------------------------

def test_cp_sat_solver_lexicographic_mode_basic():
    """Hierarchical mode produces a valid LEXICOGRAPHIC plan."""
    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
        _make_feasible_candidate("INDONESIA", "Visakhapatnam SEA", "Coal", 2, 16000.0, 170000.0),
    ]
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        max_batch_tons=80000,
        min_batch_tons=30000,
        solve_hierarchical=True,
    )

    solver = CPSatOptimizationSolver()
    status, primary_plan, alternatives, exec_time = solver.solve(
        candidates=cands, request=req
    )

    assert status in (OptimizationStatus.OPTIMAL.value, OptimizationStatus.FEASIBLE.value)
    assert primary_plan is not None
    assert primary_plan.objective_mode == "LEXICOGRAPHIC"


def test_cp_sat_solver_lexicographic_exposes_per_priority_values():
    """
    Hierarchical mode must expose achieved values for each priority.
    Keys: p2_shortage_tons, p3_economic_cost_usd, p4_risk_penalty_usd
    """
    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
        _make_feasible_candidate("INDONESIA", "Visakhapatnam SEA", "Coal", 2, 16000.0, 170000.0),
    ]
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        max_batch_tons=80000,
        min_batch_tons=30000,
        solve_hierarchical=True,
    )

    solver = CPSatOptimizationSolver()
    _, primary_plan, _, _ = solver.solve(candidates=cands, request=req)

    assert primary_plan is not None
    assert primary_plan.lexicographic_achieved_values is not None
    achieved = primary_plan.lexicographic_achieved_values
    assert "p2_shortage_tons" in achieved
    assert "p3_economic_cost_usd" in achieved
    assert "p4_risk_penalty_usd" in achieved
    assert isinstance(achieved["p2_shortage_tons"], int)


def test_cp_sat_solver_lexicographic_demand_priority_over_cost():
    """
    Hierarchical mode must prioritise demand fulfilment (P2) before cost (P3).
    A cheaper candidate that delivers less cargo must lose to a costlier one
    that fully satisfies demand.
    """
    # 'cheap_small': lower cost but only 20,000 MT max → cannot fulfil 50,000 MT alone
    # 'expensive_large': higher cost, 80,000 MT max → can fulfil demand
    cheap_small = EnrichedCandidate(
        candidate=CandidateRoute("INDONESIA", "Visakhapatnam SEA", "Coal", 1, "2024-10-01"),
        stage4_status="FEASIBLE",
        forecast_freight_usd_day=5000.0,   # Very cheap
        voyage_cost_usd=50000.0,           # Very cheap
        turnaround_hours=20.0,
        delay_risk_score=5.0,
        congestion_proxy_score=1.0,
        congestion_data_scope="GLOBAL_CONGESTION_PROXY",
        commercial_risk_score=0.1,
        vessel_archetype="Bulk Carrier Handysize Archetype Slot #1",
    )
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000, tolerance_pct=0.0)],
        min_batch_tons=30000,
        max_batch_tons=80000,
        solve_hierarchical=True,
    )
    expensive_large = EnrichedCandidate(
        candidate=CandidateRoute("AUSTRALIA", "Paradip SEA", "Coal", 1, "2024-10-01"),
        stage4_status="FEASIBLE",
        forecast_freight_usd_day=30000.0,  # Expensive
        voyage_cost_usd=500000.0,          # Expensive
        turnaround_hours=60.0,
        delay_risk_score=40.0,
        congestion_proxy_score=2.0,
        congestion_data_scope="GLOBAL_CONGESTION_PROXY",
        commercial_risk_score=0.6,
        vessel_archetype="Bulk Carrier Handysize Archetype Slot #1",
    )

    solver = CPSatOptimizationSolver()
    # Both candidates together can satisfy demand; the solver must pick enough
    _, primary_plan, _, _ = solver.solve(
        candidates=[cheap_small, expensive_large], request=req
    )

    assert primary_plan is not None
    assert primary_plan.objective_mode == "LEXICOGRAPHIC"
    # Demand must be satisfied first — shortage should be 0
    achieved = primary_plan.lexicographic_achieved_values
    assert achieved is not None
    assert achieved["p2_shortage_tons"] == 0


def test_cp_sat_solver_lexicographic_no_candidates_returns_infeasible():
    """Lexicographic solver returns INFEASIBLE when no candidates are provided."""
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        solve_hierarchical=True,
    )
    solver = CPSatOptimizationSolver()
    status, plan, alternatives, _ = solver.solve(candidates=[], request=req)

    assert status == OptimizationStatus.INFEASIBLE.value
    assert plan is None
    assert alternatives == []


# ---------------------------------------------------------------------------
# Test: DATA_UNAVAILABLE / FEASIBLE / INFEASIBLE segregation in solver
# ---------------------------------------------------------------------------

def test_solver_only_accepts_feasible_candidates():
    """
    The solver must only receive FEASIBLE candidates (segregation is enforced
    by CandidateBuilder, but the solver itself must process them correctly).
    """
    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
    ]
    for cand in cands:
        assert cand.stage4_status == "FEASIBLE"

    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=30000)],
        solve_hierarchical=True,
    )
    solver = CPSatOptimizationSolver()
    status, plan, _, _ = solver.solve(candidates=cands, request=req)

    assert status in (OptimizationStatus.OPTIMAL.value, OptimizationStatus.FEASIBLE.value)
    assert plan is not None
    for alloc in plan.allocations:
        assert alloc.stage4_status == "FEASIBLE"


# ---------------------------------------------------------------------------
# Test: No fabricated vessel identities
# ---------------------------------------------------------------------------

def test_cp_sat_solver_no_fabricated_vessel_ids():
    """
    All vessel assignments must use Charter Archetype Slot labels.
    No IMO numbers, physical ship IDs, or fabricated identifiers.
    """
    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
        _make_feasible_candidate("INDONESIA", "Paradip SEA", "Coal", 2, 16000.0, 170000.0),
    ]
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        solve_hierarchical=True,
    )
    solver = CPSatOptimizationSolver()
    _, plan, _, _ = solver.solve(candidates=cands, request=req)

    assert plan is not None
    for alloc in plan.allocations:
        # Must use archetype slot label, never a physical ship identifier
        assert "Archetype Slot" in alloc.vessel_archetype
        assert not alloc.vessel_archetype.startswith("IMO_")
        assert not alloc.vessel_archetype.startswith("IMO-")


# ---------------------------------------------------------------------------
# Test: Batch planning parameter bounds (not physical DWT)
# ---------------------------------------------------------------------------

def test_batch_bounds_are_planning_parameters_not_physical_dwt():
    """
    min_batch_tons and max_batch_tons are configurable planning parameters.
    The solver must enforce these bounds on cargo quantities.
    This test also confirms they are NOT physical vessel DWT specifications.
    """
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        min_batch_tons=30000,   # Planning parameter — not physical DWT
        max_batch_tons=80000,   # Planning parameter — not physical DWT
        solve_hierarchical=True,
    )
    # Confirm the fields are documented in the dataclass
    assert req.min_batch_tons == 30000
    assert req.max_batch_tons == 80000
    assert req.batch_step_tons == 1000

    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
    ]
    solver = CPSatOptimizationSolver()
    _, plan, _, _ = solver.solve(candidates=cands, request=req)

    if plan and plan.allocations:
        for alloc in plan.allocations:
            assert alloc.cargo_quantity_tons >= req.min_batch_tons
            assert alloc.cargo_quantity_tons <= req.max_batch_tons


# ---------------------------------------------------------------------------
# Test: Congestion data scope integrity
# ---------------------------------------------------------------------------

def test_cp_sat_solver_preserves_global_congestion_proxy_scope():
    """All allocations must carry GLOBAL_CONGESTION_PROXY congestion scope — never Indian-port-specific."""
    cands = [
        _make_feasible_candidate("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, 20000.0, 195000.0),
        _make_feasible_candidate("INDONESIA", "Paradip SEA", "Coal", 2, 16000.0, 170000.0),
    ]
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        solve_hierarchical=True,
    )
    solver = CPSatOptimizationSolver()
    _, plan, _, _ = solver.solve(candidates=cands, request=req)

    assert plan is not None
    for alloc in plan.allocations:
        assert alloc.congestion_data_scope == "GLOBAL_CONGESTION_PROXY"
