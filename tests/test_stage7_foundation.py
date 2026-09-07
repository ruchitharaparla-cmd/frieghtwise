"""
Tests for FreightWise Stage 7.1 â€” AI Agents + RAG foundation.

Verifies data contracts, serialization, missing value preservation,
data scope boundaries, safety validation rules, context immutability,
and provenance tracking.
"""

import pytest

from src.agents.contracts import (
    EvidenceItem,
    AgentContext,
    AgentRequest,
    AgentResponse,
    ProvenanceRecord,
)
from src.agents.context import build_agent_context
from src.agents.provenance import (
    create_provenance_record,
    attach_provenance_to_evidence,
    extract_provenance_chain,
)
from src.agents.safety import (
    validate_agent_response,
    verify_authoritative_immutability,
    verify_data_scope,
    verify_data_unavailability,
    SafetyCheckResult,
)


def test_1_contracts_serialize_correctly():
    """Test 1: Dataclass contracts serialize to dictionary and deserialize accurately."""
    prov = ProvenanceRecord(
        record_id="prov-101",
        source="Stage2ForecastService",
        source_type="MODEL",
        stage="Stage 2",
        model_name="XGBoostFreight",
        model_version="1.0.0",
        data_scope="GLOBAL_FREIGHT",
    )
    ev = EvidenceItem(
        evidence_id="ev-101",
        content="Predicted rate: 12500 USD/day",
        source="src/forecasting",
        source_type="FORECAST",
        relevance=0.95,
        provenance=prov,
    )
    ctx = AgentContext(
        freight_forecast={"predicted_freight_rate": 12500.0, "unit": "USD/day"},
        evidence=[ev],
    )
    req = AgentRequest(
        agent_name="CharterAdvisorAgent",
        question="What is the forecasted freight rate?",
        context=ctx,
        retrieved_evidence=[ev],
    )
    resp = AgentResponse(
        answer="The forecasted rate is 12,500 USD/day based on Stage 2 outputs.",
        evidence=[ev],
        limitations=["Subject to market volatility."],
        provenance=prov,
        status="SUCCESS",
        confidence="HIGH",
    )

    # Test serialization
    req_dict = req.to_dict()
    resp_dict = resp.to_dict()

    assert req_dict["agent_name"] == "CharterAdvisorAgent"
    assert req_dict["context"]["freight_forecast"]["predicted_freight_rate"] == 12500.0
    assert resp_dict["answer"] == "The forecasted rate is 12,500 USD/day based on Stage 2 outputs."

    # Test deserialization
    req_restored = AgentRequest.from_dict(req_dict)
    resp_restored = AgentResponse.from_dict(resp_dict)

    assert req_restored.agent_name == req.agent_name
    assert req_restored.context.freight_forecast == ctx.freight_forecast
    assert resp_restored.answer == resp.answer
    assert resp_restored.provenance.model_name == "XGBoostFreight"


def test_2_missing_values_remain_none():
    """Test 2: Missing fields in AgentContext remain None and are not filled with defaults."""
    ctx = build_agent_context(
        stage2_output={"predicted_freight_rate": 15000.0},
        # stage3, stage4, stage5, stage6 outputs omitted
    )

    assert ctx.freight_forecast == {"predicted_freight_rate": 15000.0}
    assert ctx.delay_prediction is None
    assert ctx.congestion_prediction is None
    assert ctx.feasibility_result is None
    assert ctx.cost_result is None
    assert ctx.optimization_result is None

    # Dictionary serialization preserves None
    d = ctx.to_dict()
    assert d["delay_prediction"] is None
    assert d["cost_result"] is None


def test_3_data_unavailable_is_preserved():
    """Test 3: DATA_UNAVAILABLE status from Stage 4/6 is preserved explicitly in context."""
    stage4_out = {
        "candidate_id": "cand-001",
        "status": "DATA_UNAVAILABLE",
        "unmet_constraint": "port_draft_depth",
        "details": "Vessel draft requirement unverified due to missing port channel depth data",
    }
    ctx = build_agent_context(stage4_output=stage4_out)

    assert ctx.feasibility_result["status"] == "DATA_UNAVAILABLE"

    # Verify safety check confirms preservation
    unavail_res = verify_data_unavailability(ctx)
    assert unavail_res.is_valid


def test_4_global_congestion_proxy_is_preserved():
    """Test 4: GLOBAL_CONGESTION_PROXY data scope is explicitly preserved in context."""
    stage3_out = {
        "predicted_congestion_index": 4.2,
        "high_congestion_risk": True,
        "data_scope": "GLOBAL_CONGESTION_PROXY",
    }
    ctx = build_agent_context(stage3_output=stage3_out)

    assert ctx.congestion_prediction is not None
    assert ctx.congestion_prediction["data_scope"] == "GLOBAL_CONGESTION_PROXY"
    assert ctx.congestion_prediction["predicted_congestion_index"] == 4.2


def test_5_indian_congestion_cannot_be_represented_as_verified():
    """Test 5: Safety validator rejects representing GLOBAL_CONGESTION_PROXY as verified Indian congestion."""
    ctx = build_agent_context(
        stage3_output={
            "predicted_congestion_index": 4.2,
            "data_scope": "GLOBAL_CONGESTION_PROXY",
        }
    )

    # Direct scope claim check
    res1 = verify_data_scope("VERIFIED_INDIAN_PORT_CONGESTION", context=ctx)
    assert not res1.is_valid
    assert any("GLOBAL_CONGESTION_PROXY" in v for v in res1.violations)

    # Response text check claiming actual Indian port congestion
    resp = AgentResponse(
        answer="The verified Indian port congestion index at Paradip is 4.2.",
        confidence="HIGH",
    )
    res2 = validate_agent_response(resp, context=ctx)
    assert not res2.is_valid
    assert any("GLOBAL_CONGESTION_PROXY" in v for v in res2.violations)


def test_6_authoritative_forecast_cannot_be_modified():
    """Test 6: Authoritative Stage 2 freight forecast cannot be altered through agent context or response."""
    orig_ctx = build_agent_context(
        stage2_output={"predicted_freight_rate": 14000.0, "unit": "USD/day"}
    )

    mod_ctx = build_agent_context(
        stage2_output={"predicted_freight_rate": 18000.0, "unit": "USD/day"}
    )

    res = verify_authoritative_immutability(orig_ctx, mod_ctx)
    assert not res.is_valid
    assert any("modified from 14000.0 to 18000.0" in v for v in res.violations)

    # Rejection of text claiming forecast modification
    resp = AgentResponse(
        answer="I adjusted freight forecast rate from 14,000 to 18,000 USD/day."
    )
    res_resp = validate_agent_response(resp, orig_ctx)
    assert not res_resp.is_valid
    assert any("LLM agents must not modify or recalculate" in v for v in res_resp.violations)


def test_7_authoritative_optimization_result_cannot_be_modified():
    """Test 7: Authoritative Stage 6 optimization result cannot be modified or overridden."""
    orig_ctx = build_agent_context(
        stage6_output={
            "status": "OPTIMAL",
            "allocated_tons": 50000,
            "total_cost_usd": 750000.0,
        }
    )

    mod_ctx = build_agent_context(
        stage6_output={
            "status": "OPTIMAL",
            "allocated_tons": 60000,  # modified!
            "total_cost_usd": 750000.0,
        }
    )

    res = verify_authoritative_immutability(orig_ctx, mod_ctx)
    assert not res.is_valid
    assert any("allocated_tons" in v for v in res.violations)


def test_8_provenance_is_preserved():
    """Test 8: Provenance records are properly generated, attached to evidence, and extracted."""
    prov = create_provenance_record(
        source="Stage3DelayService",
        source_type="MODEL",
        stage="Stage 3",
        model_name="LightGBMDelayModel",
        model_version="2.1.0",
        data_scope="EAST_COAST_INDIA",
    )
    ev = EvidenceItem(
        evidence_id="ev-delay-01",
        content="Turnaround delay expected: 18.5 hours",
        source="src/delays",
        source_type="DELAY",
    )
    attach_provenance_to_evidence(ev, prov)

    assert ev.provenance is not None
    assert ev.provenance.model_name == "LightGBMDelayModel"
    assert ev.provenance.data_scope == "EAST_COAST_INDIA"

    # Extract chain
    ctx = AgentContext(evidence=[ev])
    chain = extract_provenance_chain(ctx)
    assert len(chain) == 1
    assert chain[0].source == "Stage3DelayService"


def test_9_evidence_items_serialize_correctly():
    """Test 9: Evidence items with nested provenance serialize and deserialize accurately."""
    prov = create_provenance_record(
        source="Stage4FeasibilityEvaluator",
        source_type="RULE_ENGINE",
        stage="Stage 4",
        data_scope="EAST_COAST_INDIA",
    )
    ev = EvidenceItem(
        evidence_id="ev-feasibility-01",
        content="Vessel-Cargo compatibility rule passed",
        source="src/feasibility",
        source_type="FEASIBILITY",
        relevance=0.88,
        metadata={"rule_id": "R001"},
        provenance=prov,
    )

    ev_dict = ev.to_dict()
    assert ev_dict["evidence_id"] == "ev-feasibility-01"
    assert ev_dict["provenance"]["stage"] == "Stage 4"
    assert ev_dict["metadata"]["rule_id"] == "R001"

    ev_restored = EvidenceItem.from_dict(ev_dict)
    assert ev_restored.evidence_id == ev.evidence_id
    assert ev_restored.provenance.source == "Stage4FeasibilityEvaluator"
    assert ev_restored.relevance == 0.88


def test_10_safety_validation_rejects_unsupported_claims():
    """Test 10: Safety validation rejects unsupported numerical claims, fake vessel DWT/LOA/draft, and fake bunker fees."""
    # 1. Unsupported vessel DWT / draft claims
    r1 = AgentResponse(
        answer="Selected vessel IMO 9876543 has verified vessel dwt of 75,000 MT and 14m draft."
    )
    res1 = validate_agent_response(r1)
    assert not res1.is_valid
    assert any("Individual vessel DWT/LOA/beam/draft data is unavailable" in v for v in res1.violations)

    # 2. Unsupported bunker surcharge / port fee claim
    r2 = AgentResponse(
        answer="I added a custom bunker surcharge usd of $25,000 to the voyage cost."
    )
    res2 = validate_agent_response(r2)
    assert not res2.is_valid
    assert any("LLM agents must not calculate, fabricate, or override cost components" in v for v in res2.violations)

    # 3. Converting DATA_UNAVAILABLE status to numbers
    r3 = AgentResponse(
        answer="I converted DATA_UNAVAILABLE to a numerical value of 12.5 meters draft depth."
    )
    res3 = validate_agent_response(r3)
    assert not res3.is_valid
    assert any("DATA_UNAVAILABLE status cannot be converted" in v for v in res3.violations)
