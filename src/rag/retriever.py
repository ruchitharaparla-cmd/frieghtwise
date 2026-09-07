"""Stage 7.3 RAG Evidence Retriever and Retrieval Result Contracts."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from src.rag.embeddings import BaseEmbeddingModel, get_default_embedding_model
from src.rag.query import RetrievalQuery
from src.rag.vector_store import ChromaVectorStore


@dataclass
class RetrievedChunk:
    """A single retrieved evidence chunk with distance and relevance scores."""

    chunk_id: str
    document_id: str
    text: str
    distance: float
    relevance: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievedChunk":
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            text=data["text"],
            distance=data["distance"],
            relevance=data["relevance"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class RetrievalResult:
    """Structured result set containing retrieved evidence chunks and provenance metadata."""

    query: str
    results: List[RetrievedChunk] = field(default_factory=list)
    total_results: int = 0
    collection_name: str = "freightwise_knowledge_base"
    embedding_model: str = "UNASSIGNED"
    embedding_dimension: int = 0
    retrieval_status: str = "SUCCESS"
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["results"] = [r.to_dict() for r in self.results]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        raw_results = data.get("results", [])
        results = [RetrievedChunk.from_dict(r) for r in raw_results]
        return cls(
            query=data["query"],
            results=results,
            total_results=data.get("total_results", len(results)),
            collection_name=data.get("collection_name", "freightwise_knowledge_base"),
            embedding_model=data.get("embedding_model", "UNASSIGNED"),
            embedding_dimension=data.get("embedding_dimension", 0),
            retrieval_status=data.get("retrieval_status", "SUCCESS"),
            limitations=data.get("limitations", []),
        )


def calculate_relevance(distance: float) -> float:
    """Convert raw vector distance (cosine) to a deterministic relevance score in [0.0, 1.0].

    Cosine distance d is in range [0, 2].
    Relevance is calculated as max(0.0, 1.0 - (distance / 2.0)).
    """
    rel = 1.0 - (distance / 2.0)
    return round(max(0.0, min(1.0, rel)), 6)


class RAGRetriever:
    """RAG Evidence Retriever service using ChromaDB vector store."""

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "freightwise_knowledge_base",
        embedding_model: Optional[BaseEmbeddingModel] = None,
        is_testing: bool = False,
    ):
        self.embedding_model = embedding_model or get_default_embedding_model(is_testing=is_testing)
        self.vector_store = vector_store or ChromaVectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_model=self.embedding_model,
        )

    def _verify_embedding_compatibility() -> None:
        """Verify that retriever embedding model dimension matches indexed vector store records."""
        if self.vector_store.get_chunk_count() == 0:
            return

        # Fetch sample item to inspect stored embedding metadata
        sample_res = self.vector_store.collection.get(limit=1, include=["metadatas"])
        if sample_res and sample_res.get("metadatas") and len(sample_res["metadatas"]) > 0:
            stored_meta = sample_res["metadatas"][0]
            stored_dim = stored_meta.get("embedding_dimension")
            if stored_dim is not None and int(stored_dim) != self.embedding_model.vector_dimension:
                raise ValueError(
                    f"Incompatible embedding configuration. Indexed collection dimension is {stored_dim}, "
                    f"but retriever model dimension is {self.embedding_model.vector_dimension}."
                )

    def retrieve(self, query_input: Union[str, RetrievalQuery]) -> RetrievalResult:
        """Retrieve evidence chunks for a query strictly without natural-language answer generation.

        Args:
            query_input: String query or RetrievalQuery object.

        Returns:
            Structured RetrievalResult containing retrieved evidence chunks.
        """
        # 1. Parse and validate query
        if isinstance(query_input, str):
            req_query = RetrievalQuery(query=query_input)
        elif isinstance(query_input, RetrievalQuery):
            req_query = query_input
            req_query.validate()
        else:
            raise ValueError("Query input must be a string or RetrievalQuery object.")

        limitations = [
            "Retrieval layer only; does not generate natural language answers.",
            "Must NOT alter core numerical outputs, feasibility, or optimization decisions."
        ]

        # 2. Check for empty collection
        if self.vector_store.get_chunk_count() == 0:
            return RetrievalResult(
                query=req_query.query,
                results=[],
                total_results=0,
                collection_name=self.vector_store.collection_name,
                embedding_model=self.embedding_model.model_name,
                embedding_dimension=self.embedding_model.vector_dimension,
                retrieval_status="EMPTY_COLLECTION",
                limitations=limitations,
            )

        # 3. Verify embedding dimension compatibility
        if self.vector_store.get_chunk_count() > 0:
            sample_res = self.vector_store.collection.get(limit=1, include=["metadatas"])
            if sample_res and sample_res.get("metadatas") and len(sample_res["metadatas"]) > 0:
                stored_meta = sample_res["metadatas"][0]
                stored_dim = stored_meta.get("embedding_dimension")
                if stored_dim is not None and int(stored_dim) != self.embedding_model.vector_dimension:
                    raise ValueError(
                        f"Incompatible embedding configuration. Indexed collection dimension is {stored_dim}, "
                        f"but retriever model dimension is {self.embedding_model.vector_dimension}."
                    )

        # 4. Perform vector search in ChromaDB
        raw_results = self.vector_store.query(
            query_text=req_query.query,
            top_k=req_query.top_k,
            where=req_query.filters,
        )

        retrieved_chunks: List[RetrievedChunk] = []
        for item in raw_results:
            dist = float(item.get("distance", 0.0))
            rel = calculate_relevance(dist)

            # Apply minimum relevance threshold filter
            if rel >= req_query.min_relevance:
                chunk_id = item["chunk_id"]
                meta = item.get("metadata", {})
                doc_id = meta.get("document_id", "")

                chunk = RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    text=item.get("text", ""),
                    distance=dist,
                    relevance=rel,
                    metadata=meta,
                )
                retrieved_chunks.append(chunk)

        # 5. Deterministic sorting: highest relevance first, tie-break by chunk_id ascending
        retrieved_chunks.sort(key=lambda x: (-x.relevance, x.chunk_id))

        status = "SUCCESS" if len(retrieved_chunks) > 0 else "NO_RELEVANT_EVIDENCE"

        return RetrievalResult(
            query=req_query.query,
            results=retrieved_chunks,
            total_results=len(retrieved_chunks),
            collection_name=self.vector_store.collection_name,
            embedding_model=self.embedding_model.model_name,
            embedding_dimension=self.embedding_model.vector_dimension,
            retrieval_status=status,
            limitations=limitations,
        )
