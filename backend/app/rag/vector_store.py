"""Stage 7.2 ChromaDB Persistent Vector Store integration."""

import os
from typing import Any, Dict, List, Optional

import chromadb

from app.rag.contracts import DocumentChunk
from app.rag.embeddings import BaseEmbeddingModel, get_default_embedding_model


class ChromaVectorStore:
    """ChromaDB vector store for storing and querying RAG document chunks."""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "freightwise_knowledge_base",
        embedding_model: Optional[BaseEmbeddingModel] = None
    ):
        self.persist_directory = os.path.abspath(persist_directory)
        self.collection_name = collection_name
        self.embedding_model = embedding_model or get_default_embedding_model()

        # Initialize ChromaDB persistent client
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _prepare_metadata(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """Ensure all required metadata fields are populated with ChromaDB-compatible primitives."""
        raw_meta = dict(chunk.metadata) if chunk.metadata else {}

        meta: Dict[str, Any] = {
            "document_id": str(chunk.document_id),
            "chunk_id": str(chunk.chunk_id),
            "filename": str(raw_meta.get("filename", "")),
            "source": str(raw_meta.get("source", "INTERNAL")),
            "stage": str(raw_meta.get("stage", "Stage 7.2")),
            "document_type": str(raw_meta.get("document_type", "TEXT")),
            "checksum": str(raw_meta.get("checksum", "")),
            "chunk_index": int(chunk.chunk_index),
            "embedding_model": str(self.embedding_model.model_name),
            "embedding_dimension": int(self.embedding_model.vector_dimension),
        }

        # Include additional scalar metadata items if present
        for k, v in raw_meta.items():
            if k not in meta and isinstance(v, (str, int, float, bool)):
                meta[k] = v

        return meta

    def upsert_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Upsert a list of DocumentChunks into ChromaDB collection deterministically.

        Returns:
            Number of chunks successfully upserted.
        """
        if not chunks:
            return 0

        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            texts.append(chunk.text)
            metadatas.append(self._prepare_metadata(chunk))

        # Generate embeddings using configured model
        embeddings = self.embedding_model.embed_documents(texts)

        # Upsert into ChromaDB (overwrites duplicates cleanly)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        return len(chunks)

    def get_chunk_count(self) -> int:
        """Return total number of chunks indexed in the collection."""
        return self.collection.count()

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by its chunk_id."""
        res = self.collection.get(ids=[chunk_id], include=["documents", "metadatas", "embeddings"])
        if res and res.get("ids") and len(res["ids"]) > 0:
            doc = res["documents"][0] if res.get("documents") else ""
            meta = res["metadatas"][0] if res.get("metadatas") else {}
            emb = res["embeddings"][0] if res.get("embeddings") is not None and len(res["embeddings"]) > 0 else None
            return {
                "chunk_id": chunk_id,
                "text": doc,
                "metadata": meta,
                "embedding": emb,
            }
        return None

    def get_chunks_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks belonging to a document_id."""
        res = self.collection.get(
            where={"document_id": document_id},
            include=["documents", "metadatas"]
        )
        results: List[Dict[str, Any]] = []
        if res and res.get("ids"):
            for i in range(len(res["ids"])):
                results.append({
                    "chunk_id": res["ids"][i],
                    "text": res["documents"][i],
                    "metadata": res["metadatas"][i],
                })
        return sorted(results, key=lambda x: x["metadata"].get("chunk_index", 0))

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic similarity search against indexed chunks with optional metadata filtering."""
        if not query_text or self.get_chunk_count() == 0:
            return []

        query_vector = self.embedding_model.embed_query(query_text)
        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": min(top_k, self.get_chunk_count()),
            "include": ["documents", "metadatas", "distances"]
        }
        if where:
            query_kwargs["where"] = where

        res = self.collection.query(**query_kwargs)

        results: List[Dict[str, Any]] = []
        if res and res.get("ids") and len(res["ids"]) > 0:
            ids = res["ids"][0]
            docs = res["documents"][0]
            metas = res["metadatas"][0]
            dists = res["distances"][0] if res.get("distances") else [0.0] * len(ids)

            for i in range(len(ids)):
                results.append({
                    "chunk_id": ids[i],
                    "text": docs[i],
                    "metadata": metas[i],
                    "distance": dists[i],
                })
        return results
