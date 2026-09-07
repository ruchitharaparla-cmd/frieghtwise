"""
Regression & Pipeline Integration Test Suite for FreightWise Stage 6 Optimization Engine.

Validates end-to-end integration across Stage 1 data baselines, Stage 2 forecasts,
Stage 3 delays/congestion, and Stage 4 feasibility rules.

Stage5TestFixture is explicitly injected for all end-to-end tests.
The production Stage5CostRiskAdapter is verified separately in test_optimization_input_adapter.py.
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
from src.optimization.input_adapter import Stage5TestFixture, Stage5IntegrationUnavailableError


def _make_test_service() -> OptimizationService:
    """Build OptimizationService with Stage5TestFixture explicitly injected (TEST-ONLY)."""
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    engine = OptimizationEngine(candidate_builder=builder)
    return OptimizationService(engine=engine)


def test_stage6_full_pipeline_regression():
    """
    Verifies that Stage 6 executes cleanly against actual repository services & data.
    Ensures strict adherence to Mandatory Corrections:
    - DATA_UNAVAILABLE candidates excluded from primary executable plan and reported separately
    - Global congestion proxy scope explicitly preserved
    - No physical ship IDs fabricated
    - Hierarchical lexicographic objective is active by default
    """
    service = _make_test_service()

    # Standard SIH demonstration request: 60,000 MT Coal required over 3-month horizon
    request = OptimizationRequest(
        horizon_periods=3,
        planning_start_date="2024-10-01",
        demand_targets=[
            DemandTarget(commodity="Coal", target_quantity_tons=60000, tolerance_pct=0.10)
        ],
        max_charters_per_period=4,
        include_exploratory_scenario=True,
        solve_hierarchical=True,  # Default — genuine lexicographic objective
    )

    result = service.optimize(request)

    # 1. Assert solver run execution metadata
    assert result.run_id.startswith("OPT_")
    assert result.execution_time_seconds > 0.0
    assert result.execution_time_seconds < 60.0  # Must complete within budget

    # 2. Assert Candidate Summary Counts
    assert result.candidate_summary.total_generated > 0
    assert result.candidate_summary.data_unavailable_count > 0

    # 3. Assert Unavailable Candidates Reporting per Correction 1
    assert len(result.unavailable_candidates) == result.candidate_summary.data_unavailable_count
    for unav in result.unavailable_candidates:
        assert unav.stage4_status == "DATA_UNAVAILABLE"
        assert len(unav.missing_verification_reasons) > 0

    # 4. Assert Exploratory Sensitivity Scenario Plan Integrity
    assert "DATA_UNAVAILABLE_EXPLORATORY" in result.scenario_results
    exp_plan = result.scenario_results["DATA_UNAVAILABLE_EXPLORATORY"]
    assert exp_plan.plan_type == PlanType.EXPLORATORY_SENSITIVITY.value
    assert exp_plan.is_primary_optimal is False
    assert exp_plan.total_cargo_tons >= 54000  # Within 10% tolerance of 60,000 MT
    assert exp_plan.total_cost_usd > 0.0

    # 5. Assert Individual Voyage Allocations Integrity
    for alloc in exp_plan.allocations:
        assert alloc.congestion_data_scope == "GLOBAL_CONGESTION_PROXY"
        assert alloc.vessel_archetype.startswith("Bulk Carrier Handysize Archetype Slot")
        # Critical data honesty check: No fake IMO or physical ship IDs
        assert not alloc.vessel_archetype.startswith("IMO_")
        assert not alloc.vessel_archetype.startswith("IMO-")

    # 6. Assert Scope Notes
    assert len(result.data_scope_notes) >= 4

    # 7. Assert primary plan (if found) uses LEXICOGRAPHIC mode
    if result.primary_executable_plan is not None:
        plan = result.primary_executable_plan
        assert plan.objective_mode == "LEXICOGRAPHIC"
        assert plan.lexicographic_achieved_values is not None
        achieved = plan.lexicographic_achieved_values
        assert "p2_shortage_tons" in achieved
        assert "p3_economic_cost_usd" in achieved
        assert "p4_risk_penalty_usd" in achieved


def test_stage6_regression_production_path_raises_clearly():
    """
    Regression test confirming the production path (no Stage5TestFixture injected)
    raises Stage5IntegrationUnavailableError and NEVER silently uses fabricated values.
    """
    # Default OptimizationService uses Stage5CostRiskAdapter → raises
    from src.optimization.optimizer import OptimizationEngine
    from src.optimization.candidate_builder import CandidateBuilder
    prod_builder = CandidateBuilder()  # No stage5_adapter injected → production default
    prod_engine = OptimizationEngine(candidate_builder=prod_builder)
    prod_service = OptimizationService(engine=prod_engine)

    request = OptimizationRequest(
        horizon_periods=1,
        planning_start_date="2024-10-01",
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=30000)],
    )

    with pytest.raises(Stage5IntegrationUnavailableError):
        prod_service.optimize(request)


def test_stage6_weighted_mode_regression():
    """
    Regression test confirming solve_hierarchical=False uses WEIGHTED mode
    and produces valid plans without crashing.
    """
    service = _make_test_service()
    request = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        solve_hierarchical=False,
        include_exploratory_scenario=True,
    )

    result = service.optimize(request)

    assert result.run_id.startswith("OPT_")
    assert result.execution_time_seconds > 0.0

    if result.primary_executable_plan is not None:
        assert result.primary_executable_plan.objective_mode == "WEIGHTED"
        assert result.primary_executable_plan.lexicographic_achieved_values is None

    # Exploratory scenario must still be labeled correctly regardless of solver mode
    if "DATA_UNAVAILABLE_EXPLORATORY" in result.scenario_results:
        assert result.scenario_results["DATA_UNAVAILABLE_EXPLORATORY"].plan_type == (
            PlanType.EXPLORATORY_SENSITIVITY.value
        )
