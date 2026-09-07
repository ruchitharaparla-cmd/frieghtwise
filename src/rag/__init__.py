"""FreightWise Stage 7.2 RAG Ingestion & Knowledge Base Package."""

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
    get_default_embedding_model,
)
from src.rag.vector_store import ChromaVectorStore
from src.rag.ingestion import ingest_documents

__all__ = [
    "DocumentRecord",
    "DocumentChunk",
    "EmbeddingRecord",
    "IngestionResult",
    "load_document",
    "discover_and_load_documents",
    "calculate_sha256",
    "clean_text",
    "chunk_text",
    "chunk_document",
    "generate_chunk_metadata",
    "validate_chunk_metadata",
    "BaseEmbeddingModel",
    "SentenceTransformerEmbeddingModel",
    "DeterministicLocalEmbeddingModel",
    "get_default_embedding_model",
    "ChromaVectorStore",
    "ingest_documents",
]
