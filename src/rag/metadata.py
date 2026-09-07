"""Stage 7.2 Metadata generator for DocumentChunks and vector store records."""

from typing import Any, Dict, Optional
from src.rag.contracts import DocumentChunk, DocumentRecord


REQUIRED_METADATA_KEYS = [
    "document_id",
    "chunk_id",
    "filename",
    "source",
    "stage",
    "document_type",
    "checksum",
    "chunk_index",
    "embedding_model",
    "embedding_dimension",
]


def generate_chunk_metadata(
    document: DocumentRecord,
    chunk_index: int,
    total_chunks: int,
    chunk_id: str,
    embedding_model: Optional[str] = None,
    embedding_dimension: Optional[int] = None
) -> Dict[str, Any]:
    """Generate deterministic metadata dictionary for a DocumentChunk.

    All required ChromaDB metadata fields are included explicitly. Missing values remain None/unclaimed.
    """
    metadata: Dict[str, Any] = {
        "document_id": document.document_id,
        "chunk_id": chunk_id,
        "filename": document.filename,
        "source": document.source,
        "stage": document.stage,
        "document_type": document.document_type,
        "checksum": document.checksum,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "path": document.path,
        "embedding_model": embedding_model if embedding_model is not None else "UNASSIGNED",
        "embedding_dimension": embedding_dimension if embedding_dimension is not None else 0,
    }

    return metadata


def validate_chunk_metadata(metadata: Dict[str, Any]) -> bool:
    """Validate that metadata contains required ChromaDB provenance keys."""
    for key in REQUIRED_METADATA_KEYS:
        if key not in metadata:
            return False
    return True
