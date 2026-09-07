"""
Unit tests for FreightWise Stage 6 Optimization Contracts & Dataclasses.
"""

import pytest
from src.optimization.contracts import (
    DemandTarget,
    OptimizationWeights,
    OptimizationRequest,
    CandidateRoute,
    EnrichedCandidate,
    VoyageAllocation,
    OptimizationPlan,
    UnavailableCandidateReport,
    CandidateStatusSummary,
    OptimizationResult,
    OptimizationStatus,
    PlanType,
)


def test_demand_target_validation():
    dt = DemandTarget(commodity="Coal", target_quantity_tons=50000)
    assert dt.validate() is True

    with pytest.raises(ValueError):
        DemandTarget(commodity="", target_quantity_tons=50000).validate()

    with pytest.raises(ValueError):
        DemandTarget(commodity="Coal", target_quantity_tons=0).validate()


def test_optimization_request_validation():
    req = OptimizationRequest(
        horizon_periods=3,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=60000)],
    )
    assert req.validate() is True

    with pytest.raises(ValueError):
        OptimizationRequest(horizon_periods=0).validate()


def test_enriched_candidate_properties():
    # TEST-ONLY FIXTURE
    route = CandidateRoute("AUSTRALIA", "Visakhapatnam SEA", "Coal", 1, "2024-10-01")
    cand = EnrichedCandidate(candidate=route, stage4_status="FEASIBLE")
    assert cand.is_feasible is True
    assert cand.is_data_unavailable is False

    cand_unav = EnrichedCandidate(candidate=route, stage4_status="DATA_UNAVAILABLE")
    assert cand_unav.is_feasible is False
    assert cand_unav.is_data_unavailable is True


def test_optimization_result_serialization():
    # TEST-ONLY FIXTURE
    res = OptimizationResult(
        run_id="OPT_TEST_123",
        solver_status=OptimizationStatus.OPTIMAL.value,
        execution_time_seconds=0.25,
        primary_executable_plan=None,
    )
    d = res.to_dict()
    assert d["run_id"] == "OPT_TEST_123"
    assert d["solver_status"] == "OPTIMAL"
    assert d["service_version"] == "stage6_v1.0.0"
