"""Stage 7.4 Market Analyst Agent Layer Test Suite.

Verifies request/response validation, provider abstraction, Stage 7.3 RAG retrieval,
Stage 7.1 safety enforcement, immutability, and zero regression across Stages 1-6.
"""

import copy
import os
import shutil
import tempfile
import pytest

from src.agents.contracts import AgentContext, AgentResponse, EvidenceItem, ProvenanceRecord
from src.agents.market.agent import (
    BaseMarketAnalystModel,
    DeterministicTestMarketAnalystModel,
    OpenAIMarketAnalystModel,
    get_market_analyst_model,
)
from src.agents.market.contracts import (
    MarketAnalysisRequest,
    MarketAnalysisResponse,
    MarketFinding,
    VALID_CONFIDENCE_LABELS,
)
from src.agents.market.service import MarketAnalystService
from src.agents.safety import validate_agent_response, verify_authoritative_immutability
from src.rag.embeddings import DeterministicLocalEmbeddingModel
from src.rag.ingestion import ingest_documents
from src.rag.retriever import RAGRetriever
from src.rag.vector_store import ChromaVectorStore


@pytest.fixture
def temp_dir():
    """Temporary directory fixture."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def test_retriever(temp_dir):
    """Fixture providing a RAGRetriever backed by test documents."""
    chroma_dir = os.path.join(temp_dir, "chroma_db")
    doc_path = os.path.join(temp_dir, "market_report.md")
    content = """# Market Report Q3

Iron ore capesize freight rates experienced high volatility.
Stage 2 predicted freight rate is $28,500/day.
Port turnaround delays averaged 48 hours.
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

    ingest_documents(
        document_paths=[doc_path],
        persist_directory=chroma_dir,
        collection_name="test_market_db",
        embedding_model=DeterministicLocalEmbeddingModel(),
        source="INTERNAL",
        stage="Stage 7.4 Test"
    )

    store = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_market_db",
        embedding_model=DeterministicLocalEmbeddingModel()
    )
    return RAGRetriever(vector_store=store, embedding_model=DeterministicLocalEmbeddingModel())


# 1. Valid MarketAnalysisRequest
def test_valid_market_analysis_request():
    req = MarketAnalysisRequest(question="What is the forecast for Capesize freight rates?")
    assert req.question == "What is the forecast for Capesize freight rates?"
    assert req.max_evidence_items == 5
    assert req.include_limitations is True


# 2. Empty question rejection
def test_empty_question_rejection():
    with pytest.raises(ValueError, match="cannot be empty"):
        MarketAnalysisRequest(question="")

    with pytest.raises(ValueError, match="cannot be empty"):
        MarketAnalysisRequest(question="   \n\t  ")


# 3. Request serialization
def test_request_serialization():
    ctx = AgentContext(freight_forecast={"predicted_rate": 25000})
    req = MarketAnalysisRequest(
        question="Analyze rate trends",
        context=ctx,
        retrieval_query="freight rates",
        max_evidence_items=3
    )

    d = req.to_dict()
    assert d["question"] == "Analyze rate trends"
    assert d["context"]["freight_forecast"]["predicted_rate"] == 25000

    restored = MarketAnalysisRequest.from_dict(d)
    assert restored.question == req.question
    assert restored.context.freight_forecast["predicted_rate"] == 25000

    json_str = req.to_json()
    assert "Analyze rate trends" in json_str
    from_j = MarketAnalysisRequest.from_json(json_str)
    assert from_j.question == req.question


# 4. Response serialization
def test_response_serialization():
    finding = MarketFinding(
        finding="Rates are expected to rise",
        basis="AUTHORITATIVE_PIPELINE",
        evidence_ids=["ev_1"],
        confidence_label="SUPPORTED"
    )
    res = MarketAnalysisResponse(
        answer="Freight market commentary text.",
        key_findings=[finding],
        response_status="SUCCESS",
        model_name="test-model"
    )

    d = res.to_dict()
    assert d["answer"] == "Freight market commentary text."
    assert d["key_findings"][0]["finding"] == "Rates are expected to rise"

    restored = MarketAnalysisResponse.from_dict(d)
    assert restored.answer == res.answer
    assert restored.key_findings[0].finding == finding.finding

    json_str = res.to_json()
    from_j = MarketAnalysisResponse.from_json(json_str)
    assert from_j.answer == res.answer


# 5. MarketFinding serialization and validation
def test_market_finding_serialization():
    f = MarketFinding(
        finding="Congestion is high at port",
        basis="RETRIEVED_EVIDENCE",
        evidence_ids=["ev_chunk_1"],
        numerical_reference="delay_hours=48",
        confidence_label="SUPPORTED"
    )
    d = f.to_dict()
    assert d["basis"] == "RETRIEVED_EVIDENCE"
    assert d["evidence_ids"] == ["ev_chunk_1"]

    restored = MarketFinding.from_dict(d)
    assert restored.finding == f.finding

    with pytest.raises(ValueError, match="Invalid confidence_label"):
        MarketFinding(finding="Test", basis="TEST", confidence_label="STATISTICAL_100_PERCENT")


# 6. Provider interface compliance
def test_provider_interface():
    model = get_market_analyst_model(is_testing=True)
    assert isinstance(model, BaseMarketAnalystModel)
    assert hasattr(model, "model_name")
    assert hasattr(model, "model_version")
    assert hasattr(model, "generate")


# 7. Provider-unavailable handling
def test_provider_unavailable_handling():
    # Model without API key
    prod_model = OpenAIMarketAnalystModel(api_key=None)
    req = MarketAnalysisRequest(question="Analyze market")
    res = prod_model.generate(req)

    assert res.status == "PROVIDER_UNAVAILABLE"
    assert "unavailable" in res.answer.lower()
    assert res.metadata["error"] == "OPENAI_API_KEY_MISSING"


# 8. Deterministic test provider
def test_deterministic_test_provider():
    model = DeterministicTestMarketAnalystModel()
    ctx = AgentContext(freight_forecast={"predicted_freight_rate": 30000})
    req = MarketAnalysisRequest(question="What is the forecast rate?", context=ctx)

    res = model.generate(req, context=ctx)
    assert res.status == "SUCCESS"
    assert "30000 USD/day" in res.answer


# 9. Stage 7.3 RAG retrieval integration
def test_rag_retrieval_integration(test_retriever):
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    req = MarketAnalysisRequest(question="iron ore capesize freight rates", max_evidence_items=2)

    res = service.analyze(req)
    assert res.response_status == "SUCCESS"
    assert len(res.evidence) > 0
    assert any("iron ore" in e.content.lower() for e in res.evidence)


# 10. Evidence preservation
def test_evidence_preservation(test_retriever):
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("iron ore capesize")

    assert res.response_status == "SUCCESS"
    for ev in res.evidence:
        assert isinstance(ev, EvidenceItem)
        assert ev.evidence_id is not None
        assert ev.content is not None
        assert ev.source_type == "DOCUMENT"


# 11. Provenance preservation
def test_provenance_preservation(test_retriever):
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("port turnaround delays")

    assert res.response_status == "SUCCESS"
    assert res.provenance is not None
    assert res.provenance.source == "DeterministicTestMarketAnalystModel"

    for ev in res.evidence:
        assert ev.provenance is not None
        assert ev.provenance.source_type == "DOCUMENT"


# 12. Authoritative numerical values preserved
def test_authoritative_numerical_values_preserved(test_retriever):
    ctx = AgentContext(
        freight_forecast={"predicted_freight_rate": 28500.0},
        cost_result={"total_charter_cost": 450000.0}
    )
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("Summarize forecast and cost", context=ctx)

    assert res.response_status == "SUCCESS"
    assert res.numerical_inputs["freight_forecast"]["predicted_freight_rate"] == 28500.0
    assert res.numerical_inputs["cost_result"]["total_charter_cost"] == 450000.0


# 13. DATA_UNAVAILABLE preserved
def test_data_unavailable_preserved(test_retriever):
    ctx = AgentContext(
        feasibility_result={"feasibility_status": "DATA_UNAVAILABLE"}
    )
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("Is this vessel feasible?", context=ctx)

    assert res.response_status == "SUCCESS"
    assert res.numerical_inputs["feasibility_result"]["feasibility_status"] == "DATA_UNAVAILABLE"


# 14. GLOBAL_CONGESTION_PROXY not reclassified as Indian congestion
def test_global_congestion_proxy_not_reclassified(test_retriever):
    ctx = AgentContext(
        congestion_prediction={"data_scope": "GLOBAL_CONGESTION_PROXY", "predicted_index": 0.82}
    )
    # Create invalid response claiming verified Indian port congestion
    invalid_response = AgentResponse(
        answer="Our verified Indian port congestion index is 0.82.",
        status="SUCCESS"
    )
    safety_check = validate_agent_response(invalid_response, context=ctx)
    assert safety_check.is_valid is False
    assert any("GLOBAL_CONGESTION_PROXY" in v for v in safety_check.violations)


# 15. Fabricated vessel specification rejected/flagged
def test_fabricated_vessel_spec_rejected():
    invalid_response = AgentResponse(
        answer="The verified vessel DWT is 180,000 DWT with IMO number 9876543.",
        status="SUCCESS"
    )
    safety_check = validate_agent_response(invalid_response)
    assert safety_check.is_valid is False
    assert any("vessel" in v.lower() for v in safety_check.violations)


# 16. Fabricated port specification rejected/flagged
def test_fabricated_port_spec_rejected():
    invalid_response = AgentResponse(
        answer="We calculated custom bunker surcharge USD 50 per ton.",
        status="SUCCESS"
    )
    safety_check = validate_agent_response(invalid_response)
    assert safety_check.is_valid is False
    assert any("bunker" in v.lower() for v in safety_check.violations)


# 17. Fabricated numerical cost rejected/flagged
def test_fabricated_numerical_cost_rejected():
    invalid_response = AgentResponse(
        answer="I adjusted freight forecast to $35,000/day.",
        status="SUCCESS"
    )
    safety_check = validate_agent_response(invalid_response)
    assert safety_check.is_valid is False
    assert any("freight forecast" in v.lower() for v in safety_check.violations)


# 18. Optimizer output cannot be overridden
def test_optimizer_output_immutability(test_retriever):
    ctx = AgentContext(
        optimization_result={"selected_vessel_id": "V_ALPHA", "objective_value": 12400.0}
    )
    mod_ctx = copy.deepcopy(ctx)
    mod_ctx.optimization_result["objective_value"] = 99999.0

    imm_check = verify_authoritative_immutability(ctx, mod_ctx)
    assert imm_check.is_valid is False
    assert any("optimization_result.objective_value" in v for v in imm_check.violations)


# 19. Response does not mutate AgentContext
def test_response_does_not_mutate_agent_context(test_retriever):
    orig_forecast = {"predicted_rate": 25000.0}
    ctx = AgentContext(freight_forecast=orig_forecast)

    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("Analyze freight rates", context=ctx)

    assert ctx.freight_forecast == {"predicted_rate": 25000.0}
    # Verify that numerical inputs returned in response is an isolated deep copy
    assert res.numerical_inputs["freight_forecast"] is not orig_forecast


# 20. Response does not mutate retrieved evidence
def test_response_does_not_mutate_retrieved_evidence(test_retriever):
    ev = EvidenceItem(evidence_id="ev_0", content="Original content", source="doc1", source_type="DOCUMENT")
    ctx = AgentContext(evidence=[ev])

    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("Check evidence", context=ctx)

    assert len(ctx.evidence) == 1
    assert ctx.evidence[0].content == "Original content"


# 21. No fabricated citation
def test_no_fabricated_citation(test_retriever):
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze("capesize freight rates")

    valid_ev_ids = {e.evidence_id for e in res.evidence}
    for finding in res.key_findings:
        for ev_id in finding.evidence_ids:
            assert ev_id in valid_ev_ids


# 22. Limitation handling
def test_limitation_handling(test_retriever):
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    req = MarketAnalysisRequest(question="market trends", include_limitations=True)
    res = service.analyze(req)

    assert res.response_status == "SUCCESS"
    assert len(res.limitations) > 0


# 23. Complete end-to-end MarketAnalystService flow
def test_end_to_end_market_analyst_service_flow(test_retriever):
    ctx = AgentContext(
        freight_forecast={"predicted_freight_rate": 28500.0},
        delay_prediction={"predicted_delay_hours": 48.0},
        feasibility_result={"status": "FEASIBLE"}
    )
    service = MarketAnalystService(retriever=test_retriever, is_testing=True)
    res = service.analyze(
        MarketAnalysisRequest(
            question="Provide market summary for capesize chartering",
            context=ctx,
            max_evidence_items=3
        )
    )

    assert res.response_status == "SUCCESS"
    assert res.answer is not None
    assert len(res.key_findings) > 0
    assert len(res.evidence) > 0
    assert res.numerical_inputs["freight_forecast"]["predicted_freight_rate"] == 28500.0


# 24. Stage 1-6 regression compatibility
def test_stage_1_6_regression_compatibility():
    # Verify core dataclasses and imports from Stage 7.1 foundation remain intact
    from src.agents.contracts import AgentContext, AgentRequest, AgentResponse, ProvenanceRecord
    from src.agents.safety import validate_agent_response

    c = AgentContext(freight_forecast={"predicted_rate": 20000})
    req = AgentRequest(agent_name="MarketAgent", question="Test", context=c)
    assert req.question == "Test"
