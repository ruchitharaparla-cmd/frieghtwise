# FreightWise Stage 7.2 - Document Ingestion & RAG Knowledge Base Architecture

## 1. System Overview

FreightWise Stage 7.2 implements the document ingestion pipeline and ChromaDB vector database knowledge base for FreightWise. Stage 7.2 focuses exclusively on loading approved domain documentation, text cleaning, paragraph-aware chunking, metadata attachment, local embedding generation, and persistent vector storage.

Stage 7.2 does **NOT** answer user questions, run LLM inference, or implement agent orchestration. It provides the structured, deterministic knowledge base foundation that Stage 7.4 retrieval will consume.

```
FreightWise Approved Documents (.md, .txt)
                    |
                    v
           Document Loader
      (Security & Checksum SHA-256)
                    |
                    v
              Text Cleaner
  (Line Ending & Whitespace Normalization)
                    |
                    v
          Deterministic Chunker
   (Paragraph & Section Boundary Aware)
                    |
                    v
          Metadata & Provenance
   (Stage, Source, Checksum, Model Info)
                    |
                    v
         Local Embedding Engine
    (SentenceTransformers / Test Model)
                    |
                    v
        ChromaDB Vector Store
 (Persistent Storage, Idempotent Upsert)
```

---

## 2. Supported Document Types & Security Rules

### 2.1 Approved Document Formats
Ingestion is strictly restricted to text-based document formats:
* `.md` (Markdown domain documentation and stage specifications)
* `.txt` (Plain text operational logs and reference files)

### 2.2 Security & File Ingestion Restrictions
To prevent data leakage, security vulnerabilities, or invalid vector indexing, the loader strictly **rejects**:
* **Source Code**: `.py`, `.sh`, `.exe`, `.bin`
* **Data & Models**: `.csv`, `.json`, `.joblib`, `.db`, `.sqlite`, `.pkl`
* **Environment Credentials**: `.env`, `.pem`, `.key`
* **Restricted Directories**: `.git`, `venv`, `.venv`, `__pycache__`, `node_modules`, `.pytest_cache`

---

## 3. Ingestion Pipeline Stages

The ingestion pipeline (`src/rag/ingestion.py`) executes 6 deterministic steps:

1. **Discovery & Loading (`src/rag/document_loader.py`)**:
   Reads allowed files with UTF-8 encoding. Computes SHA-256 content checksums and assigns deterministic document IDs (`doc_<path_hash>_<content_hash>`).
2. **Text Cleaning (`src/rag/cleaner.py`)**:
   Normalizes line endings (`\r\n` -> `\n`), trims line-level whitespace, collapses consecutive blank lines down to 2, and preserves Markdown headers, code blocks, tables, and lists without semantic rewriting.
3. **Chunking (`src/rag/chunker.py`)**:
   Splits document text into chunks deterministically based on paragraph/heading boundaries and character limits (`chunk_size`, `chunk_overlap`). Assigns deterministic chunk IDs (`<doc_id>_chunk_<idx>`).
4. **Metadata Generation (`src/rag/metadata.py`)**:
   Attaches complete provenance and pipeline metadata to each chunk.
5. **Embedding (`src/rag/embeddings.py`)**:
   Generates dense vector embeddings using the configured local model.
6. **Vector Persistence (`src/rag/vector_store.py`)**:
   Upserts chunks into a persistent ChromaDB collection using deterministic chunk IDs.

---

## 4. Metadata & Provenance Schema

Every indexed chunk in ChromaDB preserves the following mandatory metadata fields:

| Field Name | Type | Description |
| --- | --- | --- |
| `document_id` | `str` | Deterministic unique document identifier |
| `chunk_id` | `str` | Deterministic chunk identifier (`<doc_id>_chunk_<idx>`) |
| `filename` | `str` | Original document filename |
| `source` | `str` | Provenance source attribution (e.g. `INTERNAL`) |
| `stage` | `str` | Pipeline stage attribution (e.g. `Stage 7.2`) |
| `document_type` | `str` | Document format (`MARKDOWN` or `TEXT`) |
| `checksum` | `str` | SHA-256 hex digest of uncleaned raw file content |
| `chunk_index` | `int` | Zero-based chunk position in document sequence |
| `embedding_model` | `str` | Identifier of embedding model used |
| `embedding_dimension` | `int` | Vector dimension of generated embeddings |

Missing or unknown metadata fields remain explicit rather than fabricated.

---

## 5. Local Embedding Engine Abstraction

The embedding system (`src/rag/embeddings.py`) implements a pluggable `BaseEmbeddingModel` interface:

* **Production / Default (`SentenceTransformerEmbeddingModel`)**:
  Uses `SentenceTransformers` locally (default: `all-MiniLM-L6-v2`, 384 dimensions). Never makes network API calls to OpenAI or paid services. Raises explicit errors if model dependencies are missing.
* **Testing Only (`DeterministicLocalEmbeddingModel`)**:
  Fast, test-only embedding model used strictly in unit test suites and offline test fixtures. Generates normalized 384-dimensional vectors from content hashes. **NEVER used in production.**

---

## 6. ChromaDB Vector Store & Idempotency

* **Persistent Storage**: Uses ChromaDB's `PersistentClient` targeting `./data/chroma_db`.
* **Duplicate Prevention**: Upserting relies on deterministic `chunk_id` values. Re-ingesting the exact same document set causes zero duplicate vector records.
* **Querying & Retrieval**: Supports cosine similarity search (`query()`), filtering by `document_id` (`get_chunks_by_document_id()`), and chunk retrieval by ID (`get_chunk_by_id()`).

---

## 7. Verification & Testing

Stage 7.2 is fully verified via `tests/test_stage7_2_rag_ingestion.py` covering:
1. Markdown document loading
2. Unsupported file extension rejection
3. SHA-256 content checksum determinism
4. Deterministic text cleaning
5. Deterministic text chunking
6. Sequential chunk ordering
7. Chunk ID determinism
8. Metadata preservation
9. Explicit missing metadata handling
10. Embedding model interface compliance
11. Embedding dimension consistency
12. ChromaDB persistence across restarts
13. Duplicate-safe upsert behavior
14. IngestionResult contract serialization
15. Idempotent repeated ingestion
16. Vector store directory isolation

---

## 8. Roadmap & Stage 7.4 Transition

Stage 7.2 completes the document ingestion and vector storage foundation.

* **Next (Stage 7.3)**: Knowledge base query interface & evidence formatting.
* **Stage 7.4**: RAG retrieval pipeline & LLM QA Agent synthesis.
