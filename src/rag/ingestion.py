"""Stage 7.2 RAG Ingestion Orchestrator."""

import os
from typing import List, Optional

from src.rag.chunker import chunk_document
from src.rag.cleaner import clean_text
from src.rag.contracts import DocumentChunk, DocumentRecord, IngestionResult
from src.rag.document_loader import discover_and_load_documents, load_document
from src.rag.embeddings import BaseEmbeddingModel
from src.rag.vector_store import ChromaVectorStore


def ingest_documents(
    source_directory: Optional[str] = None,
    document_paths: Optional[List[str]] = None,
    persist_directory: str = "./data/chroma_db",
    collection_name: str = "freightwise_knowledge_base",
    embedding_model: Optional[BaseEmbeddingModel] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    source: str = "INTERNAL",
    stage: str = "Stage 7.2"
) -> IngestionResult:
    """Orchestrate end-to-end document discovery, loading, cleaning, chunking, embedding, and vector persistence.

    Pipeline Steps:
    1. Discover / load DocumentRecord objects.
    2. Clean raw text using clean_text().
    3. Split text into DocumentChunk objects.
    4. Attach complete provenance metadata.
    5. Upsert into ChromaVectorStore.
    6. Return IngestionResult.
    """
    raw_docs: List[DocumentRecord] = []
    errors: List[dict] = []
    skipped_count = 0

    # 1. Discover and load documents
    if document_paths:
        for path in document_paths:
            try:
                doc = load_document(path, source=source, stage=stage)
                raw_docs.append(doc)
            except Exception as e:
                errors.append({"path": path, "error": str(e)})
                skipped_count += 1

    if source_directory and os.path.exists(source_directory):
        try:
            discovered = discover_and_load_documents(
                source_directory,
                allowed_extensions=(".md", ".txt"),
                source=source,
                stage=stage
            )
            raw_docs.extend(discovered)
        except Exception as e:
            errors.append({"source_directory": source_directory, "error": str(e)})

    # Initialize Vector Store
    vector_store = ChromaVectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name,
        embedding_model=embedding_model
    )

    all_chunks: List[DocumentChunk] = []

    # 2-4. Clean, Chunk, and Attach Metadata
    for doc in raw_docs:
        try:
            # Clean text
            cleaned_content = clean_text(doc.content)
            cleaned_doc = DocumentRecord(
                document_id=doc.document_id,
                path=doc.path,
                filename=doc.filename,
                document_type=doc.document_type,
                source=doc.source,
                stage=doc.stage,
                content=cleaned_content,
                checksum=doc.checksum,
                metadata=doc.metadata
            )

            # Chunk document
            chunks = chunk_document(cleaned_doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            all_chunks.extend(chunks)
        except Exception as e:
            errors.append({"document_id": doc.document_id, "filename": doc.filename, "error": str(e)})

    # 5. Upsert into Vector Store
    chunks_indexed = 0
    if all_chunks:
        chunks_indexed = vector_store.upsert_chunks(all_chunks)

    return IngestionResult(
        documents_processed=len(raw_docs),
        chunks_created=len(all_chunks),
        chunks_indexed=chunks_indexed,
        skipped_documents=skipped_count,
        errors=errors,
        collection_name=collection_name
    )
