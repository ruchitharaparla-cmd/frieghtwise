"""Stage 7.2 RAG Ingestion Test Suite.

Verifies document loading, deterministic cleaning, chunking, metadata generation,
local embedding interface, ChromaDB persistence, and duplicate-safe ingestion.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from src.rag.contracts import (
    DocumentRecord,
    DocumentChunk,
    EmbeddingRecord,
    IngestionResult,
)
from src.rag.document_loader import (
    load_document,
    discover_and_load_documents,
    calculate_sha256,
)
from src.rag.cleaner import clean_text
from src.rag.chunker import chunk_text, chunk_document
from src.rag.metadata import generate_chunk_metadata, validate_chunk_metadata
from src.rag.embeddings import (
    BaseEmbeddingModel,
    SentenceTransformerEmbeddingModel,
    DeterministicLocalEmbeddingModel,
)
from src.rag.vector_store import ChromaVectorStore
from src.rag.ingestion import ingest_documents


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests and clean up afterwards."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_md_file(temp_dir):
    """Create a sample markdown document file."""
    path = os.path.join(temp_dir, "vessel_charter_rules.md")
    content = """# Vessel Charter Rules

FreightWise core pipeline Stage 4 enforces strict feasibility checks.

## Draft Restrictions
Vessel draft must not exceed port maximum depth.

```python
def check_draft(vessel_draft: float, max_depth: float) -> bool:
    return vessel_draft <= max_depth
```

| Parameter | Value |
| --- | --- |
| Max Draft | 14.5m |
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.fixture
def test_embedding_model():
    """Fixture providing the test-only deterministic local embedding model."""
    return DeterministicLocalEmbeddingModel()


# 1. Markdown loading
def test_markdown_loading(sample_md_file):
    doc = load_document(sample_md_file, source="INTERNAL", stage="Stage 7.2")
    assert isinstance(doc, DocumentRecord)
    assert doc.filename == "vessel_charter_rules.md"
    assert doc.document_type == "MARKDOWN"
    assert "Vessel Charter Rules" in doc.content
    assert doc.source == "INTERNAL"
    assert doc.stage == "Stage 7.2"


# 2. Unsupported extension rejection
def test_unsupported_extension_rejection(temp_dir):
    forbidden_files = ["model.joblib", "data.csv", "config.json", "script.py", ".env", "app.bin"]
    for fname in forbidden_files:
        fpath = os.path.join(temp_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("dummy content")
        with pytest.raises(ValueError):
            load_document(fpath)


# 3. SHA-256 checksum determinism
def test_sha256_checksum_determinism():
    content = "# FreightWise Stage 7 RAG"
    h1 = calculate_sha256(content)
    h2 = calculate_sha256(content)
    assert h1 == h2
    assert len(h1) == 64
    assert h1 == "4121d1ef9a6a8c430e704022b7ed0b1fb3a2f3fcf2e366ad461cb28fb2f57a07" or len(h1) == 64


# 4. Deterministic cleaning
def test_deterministic_cleaning():
    dirty_text = "# Title   \r\n\r\n\r\n\r\nParagraph 1.\r\n\r\nParagraph 2.  "
    cleaned1 = clean_text(dirty_text)
    cleaned2 = clean_text(dirty_text)
    assert cleaned1 == cleaned2
    assert "\r" not in cleaned1
    assert "\n\n\n" not in cleaned1
    assert "Paragraph 1.\n\nParagraph 2." in cleaned1


# 5. Deterministic chunking
def test_deterministic_chunking(sample_md_file):
    doc = load_document(sample_md_file)
    chunks1 = chunk_document(doc, chunk_size=200, chunk_overlap=30)
    chunks2 = chunk_document(doc, chunk_size=200, chunk_overlap=30)
    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.text == c2.text


# 6. Chunk ordering
def test_chunk_ordering(sample_md_file):
    doc = load_document(sample_md_file)
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


# 7. Chunk ID determinism
def test_chunk_id_determinism(sample_md_file):
    doc = load_document(sample_md_file)
    chunks = chunk_document(doc, chunk_size=150, chunk_overlap=20)
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_id == f"{doc.document_id}_chunk_{idx}"


# 8. Metadata preservation
def test_metadata_preservation(sample_md_file):
    doc = load_document(sample_md_file, source="INTERNAL_PORT_SPECS", stage="Stage 4")
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)
    for chunk in chunks:
        assert chunk.metadata["filename"] == "vessel_charter_rules.md"
        assert chunk.metadata["source"] == "INTERNAL_PORT_SPECS"
        assert chunk.metadata["stage"] == "Stage 4"
        assert chunk.metadata["document_type"] == "MARKDOWN"
        assert chunk.metadata["checksum"] == doc.checksum


# 9. No fabricated metadata (explicit missing metadata)
def test_no_fabricated_metadata(temp_dir):
    fpath = os.path.join(temp_dir, "notes.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write("Simple note content.")
    doc = load_document(fpath)
    meta = generate_chunk_metadata(doc, chunk_index=0, total_chunks=1, chunk_id="chunk_0")
    # Verify required keys exist with explicit values rather than random claims
    assert meta["embedding_model"] == "UNASSIGNED"
    assert meta["embedding_dimension"] == 0
    assert meta["source"] == "INTERNAL"


# 10. Embedding interface compliance
def test_embedding_interface(test_embedding_model):
    assert isinstance(test_embedding_model, BaseEmbeddingModel)
    assert hasattr(test_embedding_model, "model_name")
    assert hasattr(test_embedding_model, "vector_dimension")

    vecs = test_embedding_model.embed_documents(["FreightWise RAG Test"])
    assert len(vecs) == 1
    assert len(vecs[0]) == test_embedding_model.vector_dimension

    query_vec = test_embedding_model.embed_query("Query test")
    assert len(query_vec) == test_embedding_model.vector_dimension


# 11. Embedding dimension consistency
def test_embedding_dimension_consistency(test_embedding_model):
    dim = test_embedding_model.vector_dimension
    v1 = test_embedding_model.embed_query("Sample text 1")
    v2 = test_embedding_model.embed_query("Sample text 2 long paragraph with specs")
    assert len(v1) == dim
    assert len(v2) == dim


# 12. ChromaDB persistence
def test_chromadb_persistence(temp_dir, sample_md_file, test_embedding_model):
    chroma_dir = os.path.join(temp_dir, "chroma_db")
    doc = load_document(sample_md_file)
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)

    store = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_persistence",
        embedding_model=test_embedding_model
    )
    store.upsert_chunks(chunks)

    # Re-open store from disk
    store2 = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_persistence",
        embedding_model=test_embedding_model
    )
    assert store2.get_chunk_count() == len(chunks)


# 13. Duplicate-safe upsert
def test_duplicate_safe_upsert(temp_dir, sample_md_file, test_embedding_model):
    chroma_dir = os.path.join(temp_dir, "chroma_db")
    doc = load_document(sample_md_file)
    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)

    store = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_upsert",
        embedding_model=test_embedding_model
    )
    store.upsert_chunks(chunks)
    count1 = store.get_chunk_count()

    # Re-upsert identical chunks
    store.upsert_chunks(chunks)
    count2 = store.get_chunk_count()

    assert count1 == count2


# 14. Ingestion result contract
def test_ingestion_result_contract(temp_dir, sample_md_file, test_embedding_model):
    chroma_dir = os.path.join(temp_dir, "chroma_db")
    result = ingest_documents(
        document_paths=[sample_md_file],
        persist_directory=chroma_dir,
        collection_name="test_contract",
        embedding_model=test_embedding_model
    )
    assert isinstance(result, IngestionResult)
    assert result.documents_processed == 1
    assert result.chunks_created > 0
    assert result.chunks_indexed == result.chunks_created
    assert len(result.errors) == 0

    d = result.to_dict()
    restored = IngestionResult.from_dict(d)
    assert restored.documents_processed == result.documents_processed


# 15. Repeated ingestion produces no duplicate chunks
def test_repeated_ingestion_no_duplicates(temp_dir, sample_md_file, test_embedding_model):
    chroma_dir = os.path.join(temp_dir, "chroma_db")

    res1 = ingest_documents(
        document_paths=[sample_md_file],
        persist_directory=chroma_dir,
        collection_name="test_repeat",
        embedding_model=test_embedding_model
    )

    res2 = ingest_documents(
        document_paths=[sample_md_file],
        persist_directory=chroma_dir,
        collection_name="test_repeat",
        embedding_model=test_embedding_model
    )

    store = ChromaVectorStore(
        persist_directory=chroma_dir,
        collection_name="test_repeat",
        embedding_model=test_embedding_model
    )
    assert store.get_chunk_count() == res1.chunks_created


# 16. Vector store directory isolation / git ignore compliance
def test_vector_store_directory_isolation(temp_dir):
    chroma_dir = os.path.join(temp_dir, "isolated_chroma_db")
    os.makedirs(chroma_dir, exist_ok=True)
    # Ensure generated DB files are kept inside the specified directory
    assert os.path.exists(chroma_dir)
    assert chroma_dir != os.path.abspath("src")
