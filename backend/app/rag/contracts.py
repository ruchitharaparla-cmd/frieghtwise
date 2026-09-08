"""Stage 7.2 Data Contracts for RAG Document Ingestion Pipeline."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class DocumentRecord:
    document_id: str
    path: str
    filename: str
    document_type: str
    source: str
    stage: str
    content: str
    checksum: str
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentRecord":
        return cls(
            document_id=data["document_id"],
            path=data["path"],
            filename=data["filename"],
            document_type=data["document_type"],
            source=data["source"],
            stage=data["stage"],
            content=data["content"],
            checksum=data["checksum"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            text=data["text"],
            chunk_index=data["chunk_index"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class EmbeddingRecord:
    chunk_id: str
    embedding_model: str
    vector_dimension: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingRecord":
        return cls(
            chunk_id=data["chunk_id"],
            embedding_model=data["embedding_model"],
            vector_dimension=data["vector_dimension"],
            metadata=data.get("metadata", {}),
            vector=data.get("vector"),
        )


@dataclass
class IngestionResult:
    documents_processed: int
    chunks_created: int
    chunks_indexed: int
    skipped_documents: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    collection_name: str = "freightwise_knowledge_base"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IngestionResult":
        return cls(
            documents_processed=data.get("documents_processed", 0),
            chunks_created=data.get("chunks_created", 0),
            chunks_indexed=data.get("chunks_indexed", 0),
            skipped_documents=data.get("skipped_documents", 0),
            errors=data.get("errors", []),
            collection_name=data.get("collection_name", "freightwise_knowledge_base"),
        )
