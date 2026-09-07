"""
Unit tests for FreightWise Stage 6 Input Adapters (Stages 2, 3, 4, and 5).

Stage 5 Isolation Tests
------------------------
This module verifies that:

A. The default production construction (Stage5CostRiskAdapter) raises
   Stage5IntegrationUnavailableError and does NOT return stub/fabricated values.

B. Stage5TestFixture works correctly when explicitly injected into tests.

C. The production optimization path (CandidateBuilder with no injected Stage 5
   adapter) fails with Stage5IntegrationUnavailableError and never silently uses
   fabricated values.
"""

import pytest
from src.optimization.input_adapter import (
    Stage2ForecastAdapter,
    Stage3DelayAdapter,
    Stage4FeasibilityAdapter,
    Stage5CostRiskAdapter,
    Stage5TestFixture,
    Stage5IntegrationUnavailableError,
)
from src.optimization.candidate_builder import CandidateBuilder
from src.optimization.contracts import OptimizationRequest, DemandTarget


# ---------------------------------------------------------------------------
# Stage 2 Adapter Tests
# ---------------------------------------------------------------------------

def test_stage2_adapter_forecast_fetch():
    adapter = Stage2ForecastAdapter()
    rate = adapter.get_forecast_rate("2024-10-01")
    assert isinstance(rate, float)
    assert rate > 0.0


# ---------------------------------------------------------------------------
# Stage 3 Adapter Tests
# ---------------------------------------------------------------------------

def test_stage3_adapter_india_port_scope_fallback():
    adapter = Stage3DelayAdapter()
    # Querying Indian port Visakhapatnam SEA triggers IndiaPortDataAbsentError internally
    metrics = adapter.predict_delay_metrics("Visakhapatnam SEA")

    assert "turnaround_hours" in metrics
    assert "delay_risk_score" in metrics
    assert metrics["congestion_data_scope"] == "GLOBAL_CONGESTION_PROXY"
    assert metrics["congestion_proxy_score"] > 0.0


def test_stage3_adapter_all_ports_return_global_proxy():
    """All ports must return GLOBAL_CONGESTION_PROXY scope — never Indian-port-specific values."""
    adapter = Stage3DelayAdapter()
    for port in ["Visakhapatnam SEA", "Paradip SEA", "Kolkata SEA"]:
        metrics = adapter.predict_delay_metrics(port)
        assert metrics["congestion_data_scope"] == "GLOBAL_CONGESTION_PROXY", (
            f"Port {port} returned scope {metrics['congestion_data_scope']!r}; "
            "expected GLOBAL_CONGESTION_PROXY"
        )


# ---------------------------------------------------------------------------
# Stage 4 Adapter Tests
# ---------------------------------------------------------------------------

def test_stage4_adapter_feasibility_check():
    adapter = Stage4FeasibilityAdapter()
    res = adapter.check_feasibility("AUSTRALIA", "Visakhapatnam SEA", "Coal")

    assert res.feasibility_status in ("FEASIBLE", "INFEASIBLE", "DATA_UNAVAILABLE")
    assert res.origin == "AUSTRALIA"
    assert res.destination == "Visakhapatnam SEA"


# ---------------------------------------------------------------------------
# Stage 5 — Audit Item A
# Production adapter must ALWAYS raise Stage5IntegrationUnavailableError
# ---------------------------------------------------------------------------

def test_stage5_production_adapter_raises_on_call():
    """
    Audit Item A: Stage5CostRiskAdapter (production) must raise
    Stage5IntegrationUnavailableError — it must NEVER return stub values.
    """
    adapter = Stage5CostRiskAdapter()
    with pytest.raises(Stage5IntegrationUnavailableError):
        adapter.calculate_cost_and_risk("AUSTRALIA", "Visakhapatnam SEA", "Coal", 24.0)


def test_stage5_production_adapter_error_message_is_informative():
    """Error message must guide the user toward the correct test injection pattern."""
    adapter = Stage5CostRiskAdapter()
    with pytest.raises(Stage5IntegrationUnavailableError) as exc_info:
        adapter.calculate_cost_and_risk("INDONESIA", "Paradip SEA", "Iron Ore", 36.0)
    assert "Stage5TestFixture" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Stage 5 — Audit Item B
# TEST-ONLY fixture works when explicitly injected
# ---------------------------------------------------------------------------

def test_stage5_test_fixture_explicit_injection_returns_values():
    """
    Audit Item B: Stage5TestFixture must return valid cost/risk values when
    explicitly injected by test code.
    """
    fixture = Stage5TestFixture()
    cost_risk = fixture.calculate_cost_and_risk("AUSTRALIA", "Visakhapatnam SEA", "Coal", 24.0)

    assert "voyage_cost_usd" in cost_risk
    assert "commercial_risk_score" in cost_risk
    assert cost_risk["voyage_cost_usd"] > 100_000.0
    assert 0.0 <= cost_risk["commercial_risk_score"] <= 1.0


def test_stage5_test_fixture_deterministic():
    """Stage5TestFixture must produce deterministic values for the same inputs."""
    fixture = Stage5TestFixture()
    result_a = fixture.calculate_cost_and_risk("RUSSIA", "Kolkata SEA", "Coal", 48.0)
    result_b = fixture.calculate_cost_and_risk("RUSSIA", "Kolkata SEA", "Coal", 48.0)
    assert result_a == result_b


def test_stage5_test_fixture_origin_differentiation():
    """Stage5TestFixture must differentiate costs by origin country."""
    fixture = Stage5TestFixture()
    aus = fixture.calculate_cost_and_risk("AUSTRALIA", "Visakhapatnam SEA", "Coal", 24.0)
    idn = fixture.calculate_cost_and_risk("INDONESIA", "Visakhapatnam SEA", "Coal", 24.0)
    rus = fixture.calculate_cost_and_risk("RUSSIA", "Visakhapatnam SEA", "Coal", 24.0)

    # Australia and Russia should cost more than Indonesia (further distances)
    assert aus["voyage_cost_usd"] > idn["voyage_cost_usd"]
    assert rus["voyage_cost_usd"] > idn["voyage_cost_usd"]


# ---------------------------------------------------------------------------
# Stage 5 — Audit Item C
# Production CandidateBuilder must NOT silently use fabricated values
# ---------------------------------------------------------------------------

def test_candidate_builder_default_raises_stage5_error():
    """
    Audit Item C: CandidateBuilder with default (no injected Stage 5 adapter)
    must propagate Stage5IntegrationUnavailableError — never silently use stub values.
    """
    builder = CandidateBuilder()  # No stage5_adapter injected → production path
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=30000)],
    )

    with pytest.raises(Stage5IntegrationUnavailableError):
        builder.build_and_filter_candidates(
            request=req,
            origins=["AUSTRALIA"],
            ports=["Visakhapatnam SEA"],
        )


def test_candidate_builder_with_test_fixture_does_not_raise():
    """
    CandidateBuilder with explicitly injected Stage5TestFixture must succeed
    and return enriched candidates.
    """
    builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    req = OptimizationRequest(
        horizon_periods=1,
        demand_targets=[DemandTarget(commodity="Coal", target_quantity_tons=30000)],
    )

    result = builder.build_and_filter_candidates(
        request=req,
        origins=["AUSTRALIA"],
        ports=["Visakhapatnam SEA"],
    )

    assert result.summary.total_generated >= 1
    # All enriched candidates must come from Stage5TestFixture, not the production adapter
    for cand in result.all_enriched_candidates:
        # voyage_cost_usd is a TEST-ONLY fixture value (>= 150,000 base)
        assert cand.voyage_cost_usd >= 150_000.0


def test_stage5_test_fixture_is_not_instance_of_production_adapter():
    """
    Stage5TestFixture must be a distinct class from Stage5CostRiskAdapter.
    It must not inherit from Stage5CostRiskAdapter.
    """
    fixture = Stage5TestFixture()
    assert not isinstance(fixture, Stage5CostRiskAdapter), (
        "Stage5TestFixture must be a separate class and must NOT inherit from Stage5CostRiskAdapter"
    )
