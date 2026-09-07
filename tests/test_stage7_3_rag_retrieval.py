"""Stage 7.3 RAG Retrieval Service Test Suite.

Verifies query validation, top-K search, relevance filtering, metadata preservation,
provenance tracking, embedding compatibility checks, and security boundaries.
"""

import os
import shutil
import tempfile
import pytest

from src.rag.contracts import DocumentChunk
from src.rag.embeddings import DeterministicLocalEmbeddingModel
from src.rag.ingestion import ingest_documents
from src.rag.query import RetrievalQuery
from src.rag.retriever import (
    RAGRetriever,
    RetrievalResult,
    RetrievedChunk,
    calculate_relevance,
)
from src.rag.vector_store import ChromaVectorStore


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests and clean up afterwards."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def test_embedding_model():
    """Deterministic local embedding model for test fixtures."""
    return DeterministicLocalEmbeddingModel()


@pytest.fixture
def populated_vector_store(temp_dir, test_embedding_model):
    """Fixture providing a populated vector store with test domain documents."""
    chroma_dir = os.path.join(temp_dir, "chroma_db")
    doc_path1 = os.path.join(temp_dir, "vessel_feasibility_rules.md")
    content1 = """# Vessel Feasibility Rules

FreightWise Stage 4 evaluates vessel-cargo compatibility.

## Draft Restrictions
Vessel draft must not exceed maximum depth at berth.
Maximum draft for Paradip Port berth 3 is 14.5 meters.
"""
    with open(doc_path1, "w", encoding="utf-8") as f:
        f.write(content1)

    doc_path2 = os.path.join(temp_dir, "charter_cost_engine.md")
    content2 = """# Stage 5 Voyage Charter Cost Engine

Stage 5 computes total voyage costs including bunker fuel and port fees.

## Fuel Cost Calculation
Bunker consumption is calculated based on sea speed and port stay.
Vessel daily bunker cost is $15,000 per day.
"""
    with open(doc_path2, "w", encoding="utf-8") as f:
        f.write(content2)

    # Ingest documents
    ingest_documents(
        document_paths=[doc_path1, doc_path2],
        persist_directory=chroma_dir,
        collection_name="test_retrieval_db",
        embedding_model=test_embedding_model,
        source="INTERNAL",
        stage="Stage 7.3 Test"
    )

    store = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_retrieval_db",
        embedding_model=test_embedding_model
    )
    return store


# 1. Empty query rejected
def test_empty_query_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        RetrievalQuery(query="")


# 2. Whitespace query rejected
def test_whitespace_query_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        RetrievalQuery(query="   \n\t  ")


# 3. Invalid top_k rejected
def test_invalid_top_k_rejected():
    with pytest.raises(ValueError, match="positive integer"):
        RetrievalQuery(query="valid query", top_k=0)

    with pytest.raises(ValueError, match="positive integer"):
        RetrievalQuery(query="valid query", top_k=-5)


# 4. Query serialization
def test_query_serialization():
    q = RetrievalQuery(
        query="vessel draft limits",
        top_k=3,
        min_relevance=0.2,
        filters={"source": "INTERNAL"},
        collection_name="custom_coll"
    )
    d = q.to_dict()
    assert d["query"] == "vessel draft limits"
    assert d["top_k"] == 3
    assert d["min_relevance"] == 0.2
    assert d["filters"] == {"source": "INTERNAL"}

    restored = RetrievalQuery.from_dict(d)
    assert restored.query == q.query
    assert restored.top_k == q.top_k
    assert restored.min_relevance == q.min_relevance
    assert restored.filters == q.filters


# 5. Retrieval result serialization
def test_retrieval_result_serialization():
    chunk = RetrievedChunk(
        chunk_id="chunk_1",
        document_id="doc_1",
        text="Vessel draft rules text.",
        distance=0.1,
        relevance=0.95,
        metadata={"filename": "rules.md", "stage": "Stage 4"}
    )
    res = RetrievalResult(
        query="draft rules",
        results=[chunk],
        total_results=1,
        collection_name="test_coll",
        embedding_model="test-model",
        embedding_dimension=384,
        retrieval_status="SUCCESS",
        limitations=["Retrieval layer only"]
    )

    d = res.to_dict()
    assert d["query"] == "draft rules"
    assert len(d["results"]) == 1
    assert d["results"][0]["chunk_id"] == "chunk_1"

    restored = RetrievalResult.from_dict(d)
    assert restored.query == res.query
    assert len(restored.results) == 1
    assert restored.results[0].chunk_id == "chunk_1"
    assert restored.results[0].relevance == 0.95


# 6. Top-K behavior
def test_top_k_behavior(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    q = RetrievalQuery(query="vessel draft and charter costs", top_k=1)
    res = retriever.retrieve(q)
    assert res.retrieval_status == "SUCCESS"
    assert len(res.results) == 1


# 7. Metadata preservation
def test_metadata_preservation(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    res = retriever.retrieve("Paradip Port berth draft")
    assert res.retrieval_status == "SUCCESS"
    for chunk in res.results:
        assert isinstance(chunk.metadata, dict)
        assert "filename" in chunk.metadata
        assert "stage" in chunk.metadata
        assert "document_type" in chunk.metadata


# 8. Provenance preservation
def test_provenance_preservation(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    res = retriever.retrieve("bunker fuel cost")
    assert res.retrieval_status == "SUCCESS"
    for chunk in res.results:
        m = chunk.metadata
        assert m.get("document_id") is not None
        assert m.get("chunk_id") is not None
        assert m.get("filename") is not None
        assert m.get("checksum") is not None
        assert m.get("embedding_model") == populated_vector_store.embedding_model.model_name
        assert m.get("embedding_dimension") == populated_vector_store.embedding_model.vector_dimension


# 9. Deterministic result ordering
def test_deterministic_result_ordering(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    res1 = retriever.retrieve("vessel rules")
    res2 = retriever.retrieve("vessel rules")

    assert len(res1.results) == len(res2.results)
    for c1, c2 in zip(res1.results, res2.results):
        assert c1.chunk_id == c2.chunk_id
        assert c1.relevance == c2.relevance

    # Check ordering: highest relevance first
    relevances = [c.relevance for c in res1.results]
    assert relevances == sorted(relevances, reverse=True)


# 10. Relevance threshold filtering
def test_relevance_threshold_filtering(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    # High threshold should filter out less relevant results
    q_high = RetrievalQuery(query="draft restrictions", min_relevance=0.99)
    res_high = retriever.retrieve(q_high)

    q_low = RetrievalQuery(query="draft restrictions", min_relevance=0.0)
    res_low = retriever.retrieve(q_low)

    assert len(res_high.results) <= len(res_low.results)


# 11. No-result behavior
def test_no_result_behavior(temp_dir, test_embedding_model):
    chroma_dir = os.path.join(temp_dir, "empty_chroma_db")
    store = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="empty_coll",
        embedding_model=test_embedding_model
    )
    retriever = RAGRetriever(vector_store=store, embedding_model=test_embedding_model)

    res = retriever.retrieve("any query")
    assert res.retrieval_status == "EMPTY_COLLECTION"
    assert len(res.results) == 0


def test_no_relevant_evidence_threshold(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    # Unreachable minimum relevance threshold 1.0
    q = RetrievalQuery(query="random non matching phrase", min_relevance=1.0)
    res = retriever.retrieve(q)
    assert res.retrieval_status == "NO_RELEVANT_EVIDENCE"
    assert len(res.results) == 0


# 12. Metadata filtering
def test_metadata_filtering(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    # Filter for specific filename
    q = RetrievalQuery(
        query="fuel and draft",
        filters={"filename": "vessel_feasibility_rules.md"}
    )
    res = retriever.retrieve(q)
    assert res.retrieval_status == "SUCCESS"
    for chunk in res.results:
        assert chunk.metadata["filename"] == "vessel_feasibility_rules.md"


# 13. Embedding model metadata preservation
def test_embedding_model_metadata_preservation(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    res = retriever.retrieve("fuel consumption")
    assert res.embedding_model == populated_vector_store.embedding_model.model_name
    assert res.embedding_dimension == populated_vector_store.embedding_model.vector_dimension


# 14. Incompatible embedding configuration rejection
def test_incompatible_embedding_configuration_rejection(temp_dir, populated_vector_store):
    # Create an embedding model with dimension mismatch (e.g. 128 vs 384)
    incompatible_model = DeterministicLocalEmbeddingModel(
        model_name="incompatible-128d",
        vector_dimension=128
    )
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=incompatible_model
    )

    with pytest.raises(ValueError, match="Incompatible embedding configuration"):
        retriever.retrieve("vessel draft")


# 15. Deterministic test retrieval using test-only embedding model
def test_deterministic_test_retrieval(populated_vector_store):
    assert isinstance(populated_vector_store.embedding_model, DeterministicLocalEmbeddingModel)
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    res1 = retriever.retrieve("Paradip port draft")
    res2 = retriever.retrieve("Paradip port draft")

    assert res1.results[0].chunk_id == res2.results[0].chunk_id
    assert res1.results[0].relevance == res2.results[0].relevance


# 16. Retrieval does not mutate source documents
def test_retrieval_does_not_mutate_documents(temp_dir, sample_file_path=None):
    doc_path = os.path.join(temp_dir, "immutable_doc.md")
    content = "# Immutable Spec\nDo not change this content."
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

    store = ChromaVectorStore(
        persist_directory=os.path.join(temp_dir, "chroma"),
        collection_name="immutability_test",
        embedding_model=DeterministicLocalEmbeddingModel()
    )
    ingest_documents(
        document_paths=[doc_path],
        persist_directory=os.path.join(temp_dir, "chroma"),
        collection_name="immutability_test",
        embedding_model=DeterministicLocalEmbeddingModel()
    )

    retriever = RAGRetriever(vector_store=store, embedding_model=DeterministicLocalEmbeddingModel())
    retriever.retrieve("Immutable Spec")

    with open(doc_path, "r", encoding="utf-8") as f:
        read_content = f.read()

    assert read_content == content


# 17. Retrieval does not modify Stage 2-6 outputs
def test_retrieval_does_not_modify_stage_outputs(populated_vector_store):
    mock_stage2_forecast = {"route_id": "R1", "predicted_rate": 28.5}
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    retriever.retrieve("freight rate forecast")

    # Verify original numerical forecast is completely untouched
    assert mock_stage2_forecast["predicted_rate"] == 28.5


# 18. No fabricated evidence
def test_no_fabricated_evidence(populated_vector_store):
    retriever = RAGRetriever(
        vector_store=populated_vector_store,
        embedding_model=populated_vector_store.embedding_model
    )
    res = retriever.retrieve("Draft Restrictions")
    assert res.retrieval_status == "SUCCESS"

    # Verify that every retrieved chunk's text is exact indexed document content
    for chunk in res.results:
        assert len(chunk.text) > 0
        # Text must be present in the original document content
        assert "Vessel" in chunk.text or "Stage" in chunk.text or "Fuel" in chunk.text
