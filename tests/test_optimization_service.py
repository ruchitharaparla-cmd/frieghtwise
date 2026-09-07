"""
Unit tests for FreightWise Stage 6 Optimization Service public API.

Stage5TestFixture is explicitly injected through OptimizationEngine → CandidateBuilder
for all tests requiring end-to-end execution.

The default production Stage5CostRiskAdapter is never silently used in tests.
"""

import pytest
from src.optimization.service import OptimizationService
from src.optimization.optimizer import OptimizationEngine
from src.optimization.candidate_builder import CandidateBuilder
from src.optimization.contracts import (
    OptimizationRequest,
    DemandTarget,
    OptimizationStatus,
    PlanType,
)
from src.optimization.input_adapter import Stage5TestFixture


def _make_test_service() -> OptimizationService:
    """Build an OptimizationService with Stage5TestFixture explicitly injected (TEST-ONLY)."""
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    engine = OptimizationEngine(candidate_builder=builder)
    return OptimizationService(engine=engine)


def test_optimization_service_end_to_end():
    """
    Tests default optimization service execution over real Stage 4 Indian port candidates.
    Per Mandatory Correction 1, Indian port candidates evaluate to DATA_UNAVAILABLE in Stage 4,
    so they are excluded from primary executable plans and reported under unavailable_candidates[].
    The exploratory scenario provides the exploratory plan.
    """
    service = _make_test_service()
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        include_exploratory_scenario=True,
    )

    res = service.optimize(req)

    assert res.run_id.startswith("OPT_")
    assert res.candidate_summary.total_generated > 0
    assert res.candidate_summary.data_unavailable_count > 0
    assert len(res.unavailable_candidates) > 0
    assert len(res.data_scope_notes) > 0

    # Verify exploratory sensitivity scenario output per Correction 1
    assert "DATA_UNAVAILABLE_EXPLORATORY" in res.scenario_results
    exp_plan = res.scenario_results["DATA_UNAVAILABLE_EXPLORATORY"]
    assert exp_plan.plan_type == PlanType.EXPLORATORY_SENSITIVITY.value
    assert exp_plan.is_primary_optimal is False
    assert exp_plan.total_cargo_tons >= 45000


def test_optimization_service_dict_wrapper():
    service = _make_test_service()
    res_dict = service.optimize_dict(
        horizon_periods=2,
        demand_targets=[{"commodity": "Coal", "target_quantity_tons": 60000}],
    )

    assert "run_id" in res_dict
    assert "solver_status" in res_dict
    assert "candidate_summary" in res_dict
    assert "unavailable_candidates" in res_dict


def test_optimization_service_lexicographic_plan_has_achieved_values():
    """
    When solve_hierarchical=True, the primary plan must expose
    lexicographic_achieved_values with p2/p3/p4 keys.
    """
    service = _make_test_service()
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        solve_hierarchical=True,
        include_exploratory_scenario=False,
    )

    res = service.optimize(req)

    # If a primary plan was found, it must be LEXICOGRAPHIC with achieved values
    if res.primary_executable_plan is not None:
        plan = res.primary_executable_plan
        assert plan.objective_mode == "LEXICOGRAPHIC"
        assert plan.lexicographic_achieved_values is not None
        achieved = plan.lexicographic_achieved_values
        assert "p2_shortage_tons" in achieved
        assert "p3_economic_cost_usd" in achieved
        assert "p4_risk_penalty_usd" in achieved


def test_optimization_service_weighted_mode_plan():
    """
    When solve_hierarchical=False, the primary plan must use WEIGHTED mode
    and must NOT expose lexicographic achieved values.
    """
    service = _make_test_service()
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        solve_hierarchical=False,
        include_exploratory_scenario=False,
    )

    res = service.optimize(req)

    if res.primary_executable_plan is not None:
        plan = res.primary_executable_plan
        assert plan.objective_mode == "WEIGHTED"
        assert plan.lexicographic_achieved_values is None
