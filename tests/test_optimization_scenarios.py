"""
Unit tests for Stage 6 Scenario Analysis & Sensitivity Evaluation Engine.

Stage5TestFixture is explicitly injected into CandidateBuilder for all tests.
The default production Stage5CostRiskAdapter is never used in this test module.
"""

import pytest
from src.optimization.contracts import OptimizationRequest, DemandTarget, PlanType
from src.optimization.candidate_builder import CandidateBuilder
from src.optimization.scenario import ScenarioEvaluator
from src.optimization.input_adapter import Stage5TestFixture


def test_scenario_evaluator_multi_scenario():
    # Explicitly inject Stage5TestFixture — TEST-ONLY
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=50000)],
        include_exploratory_scenario=True,
    )

    build_res = builder.build_and_filter_candidates(
        request=req,
        origins=["AUSTRALIA", "INDONESIA"],
        ports=["Visakhapatnam SEA"],
    )

    evaluator = ScenarioEvaluator(candidate_builder=builder)
    scenarios = evaluator.evaluate_scenarios(req, build_res)

    # Check that exploratory scenario is evaluated and labeled strictly EXPLORATORY_SENSITIVITY_PLAN
    assert "DATA_UNAVAILABLE_EXPLORATORY" in scenarios
    exp_plan = scenarios["DATA_UNAVAILABLE_EXPLORATORY"]
    assert exp_plan.plan_type == PlanType.EXPLORATORY_SENSITIVITY.value
    assert exp_plan.is_primary_optimal is False
    assert exp_plan.total_cargo_tons >= 45000
