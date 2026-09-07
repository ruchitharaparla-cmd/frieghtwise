"""
Unit tests for Candidate Route Builder & Stage 4 Strict Segregation Logic.

All tests explicitly inject Stage5TestFixture into CandidateBuilder.
The default production Stage5CostRiskAdapter is not used here; it would
raise Stage5IntegrationUnavailableError.
"""

import pytest
from src.optimization.contracts import OptimizationRequest, DemandTarget
from src.optimization.candidate_builder import CandidateBuilder, normalize_commodity_name
from src.optimization.input_adapter import Stage5TestFixture


def test_normalize_commodity_name():
    assert normalize_commodity_name("COAL,COKE AND BRIQUITTES ETC") == "Coal"
    assert normalize_commodity_name("IRON ORE") == "Iron Ore"
    assert normalize_commodity_name("FERTILEZERS MANUFACTURED") == "Fertilizers Manufactured"


def test_candidate_builder_strict_segregation():
    # Explicitly inject Stage5TestFixture — TEST-ONLY
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    req = OptimizationRequest(
        horizon_periods=2,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=60000)],
    )

    res = builder.build_and_filter_candidates(
        request=req,
        origins=["AUSTRALIA", "INDONESIA"],
        ports=["Visakhapatnam SEA", "Paradip SEA"],
    )

    assert res.summary.total_generated == 8  # 2 periods * 1 commodity * 2 origins * 2 ports

    # Verify that executable candidates contain ONLY Stage 4 FEASIBLE items
    for cand in res.executable_candidates:
        assert cand.stage4_status == "FEASIBLE"

    # Verify that unavailable candidates are collected separately
    for unav in res.unavailable_candidates:
        assert unav.stage4_status == "DATA_UNAVAILABLE"
        assert len(unav.missing_verification_reasons) > 0


def test_candidate_builder_no_fabricated_vessel_identities():
    """
    All enriched candidates must use Charter Archetype Slot labels.
    No physical ship IDs, IMO numbers, or fabricated vessel identifiers.
    """
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=30000)],
    )

    res = builder.build_and_filter_candidates(
        request=req,
        origins=["AUSTRALIA"],
        ports=["Visakhapatnam SEA"],
    )

    for cand in res.all_enriched_candidates:
        assert "Archetype Slot" in cand.vessel_archetype
        assert not cand.vessel_archetype.startswith("IMO_")
        assert not cand.vessel_archetype.startswith("IMO-")


def test_candidate_builder_data_unavailable_excluded_from_executable():
    """
    DATA_UNAVAILABLE candidates must never appear in executable_candidates.
    They must appear in unavailable_candidates only.
    """
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=30000)],
    )

    res = builder.build_and_filter_candidates(
        request=req,
        origins=["AUSTRALIA", "INDONESIA"],
        ports=["Visakhapatnam SEA"],
    )

    executable_ids = {c.candidate.candidate_id for c in res.executable_candidates}
    unavailable_ids = {r.candidate_id for r in res.unavailable_candidates}

    # No overlap — a candidate cannot be in both pools
    assert executable_ids.isdisjoint(unavailable_ids), (
        "DATA_UNAVAILABLE candidates must not appear in the executable pool."
    )

    # All unavailable have the correct status
    for unav in res.unavailable_candidates:
        assert unav.stage4_status == "DATA_UNAVAILABLE"
