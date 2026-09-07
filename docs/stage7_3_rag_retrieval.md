# FreightWise Stage 7.3 - RAG Evidence Retrieval Service Architecture

## 1. System Overview & Purpose

FreightWise Stage 7.3 implements the RAG Evidence Retrieval Service (`src/rag/retriever.py` and `src/rag/query.py`). Stage 7.3 provides the query, search, filtering, relevance scoring, and provenance-tracking retrieval layer operating on top of the Stage 7.2 ChromaDB vector store knowledge base.

Stage 7.3 is **STRICTLY AN EVIDENCE RETRIEVAL SERVICE**.

It does **NOT**:
* Generate natural-language LLM answers or responses
* Perform LLM agent orchestration or prompt completion
* Make numerical decisions, alter costs, or modify forecasts
* Override Stage 2-6 pipeline outputs or CP-SAT optimization results
* Convert `DATA_UNAVAILABLE` into numerical estimates
* Fabricate missing evidence or domain knowledge

```
User Query Input (str or RetrievalQuery)
                    |
                    v
          Query Validation Engine
 (Validates Non-Empty, top_k > 0, min_relevance)
                    |
                    v
     Embedding Compatibility Auditor
 (Verifies Retriever & ChromaDB Vector Dimension)
                    |
                    v
        ChromaDB Similarity Search
 (Cosine Search with Optional Metadata Filters)
                    |
                    v
          Relevance Score Math
 (relevance = max(0.0, 1.0 - (distance / 2.0)))
                    |
                    v
        Relevance Threshold Filter
     (Filters Out Chunks Below min_relevance)
                    |
                    v
          Deterministic Sorting
 (Sorts by Relevance Descending, chunk_id Ascending)
                    |
                    v
         Structured RetrievalResult
 (RetrievedChunk List + Provenance Metadata)
```

---

## 2. RAG Retrieval Contracts

### 2.1 RetrievalQuery (`src/rag/query.py`)
`RetrievalQuery` defines the typed, validated request contract for evidence retrieval:

| Field Name | Type | Default | Description |
| --- | --- | --- | --- |
| `query` | `str` | *Required* | Raw search text query |
| `top_k` | `int` | `5` | Maximum number of chunks to retrieve (> 0) |
| `min_relevance` | `float` | `0.0` | Minimum relevance threshold score in [0.0, 1.0] |
| `filters` | `Optional[Dict[str, Any]]` | `None` | Optional ChromaDB metadata filter dictionary |
| `collection_name` | `str` | `"freightwise_knowledge_base"` | Target ChromaDB vector store collection |

**Validation Rules**:
* Rejects empty or whitespace-only queries with `ValueError`
* Rejects `top_k <= 0` with `ValueError`
* Rejects `min_relevance` outside range [0.0, 1.0] with `ValueError`
* Supports `.to_dict()` and `.from_dict()` deterministic serialization

### 2.2 RetrievedChunk (`src/rag/retriever.py`)
Represents an individual retrieved document chunk with similarity metrics:

| Field Name | Type | Description |
| --- | --- | --- |
| `chunk_id` | `str` | Deterministic chunk ID (`<doc_id>_chunk_<idx>`) |
| `document_id` | `str` | Parent document identifier |
| `text` | `str` | Exact un-modified text snippet from indexed document |
| `distance` | `float` | Raw vector distance (cosine distance in range [0, 2]) |
| `relevance` | `float` | Deterministic relevance score in range [0.0, 1.0] |
| `metadata` | `Dict[str, Any]` | Full provenance metadata dictionary |

### 2.3 RetrievalResult (`src/rag/retriever.py`)
Represents the complete result set returned by `RAGRetriever.retrieve()`:

| Field Name | Type | Description |
| --- | --- | --- |
| `query` | `str` | Original query text string |
| `results` | `List[RetrievedChunk]` | List of retrieved evidence chunks passing threshold |
| `total_results` | `int` | Number of chunks returned in `results` |
| `collection_name` | `str` | Target vector collection name |
| `embedding_model` | `str` | Name of embedding model used for query embedding |
| `embedding_dimension` | `int` | Vector dimension of embedding model |
| `retrieval_status` | `str` | Status tag (`SUCCESS`, `NO_RELEVANT_EVIDENCE`, `EMPTY_COLLECTION`) |
| `limitations` | `List[str]` | Boundary and scope limitation statements |

---

## 3. Embedding Model Requirements

### 3.1 Production Default Model
Production retrieval utilizes `SentenceTransformerEmbeddingModel` using the local `SentenceTransformers` model (`all-MiniLM-L6-v2`, 384 dimensions).

* Network-free, local embedding generation
* Will **NEVER** silently fall back to random or zero vectors in production
* Raises an explicit `RuntimeError` if model dependencies are missing

### 3.2 Testing-Only Embedding Model
`DeterministicLocalEmbeddingModel` generates fast, deterministic 384-dimensional unit vectors from text hashes.
* **FOR UNIT TESTS AND TEST FIXTURES ONLY**
* Must **NEVER** be used as the production retrieval embedding model

### 3.3 Embedding Compatibility Auditing
Before executing ChromaDB queries, `RAGRetriever` inspects the indexed vector store collection metadata. If the retriever embedding model dimension does not match the stored vector dimension in ChromaDB, `RAGRetriever` raises an explicit `ValueError`:

```
Incompatible embedding configuration. Indexed collection dimension is 384, but retriever model dimension is 128.
```

---

## 4. Search, Relevance, and Filtering Logic

### 4.1 Similarity Search & Top-K
Queries are embedded via `embedding_model.embed_query(query)`. ChromaDB searches vector space using cosine distance, selecting up to `top_k` candidate chunks.

### 4.2 Relevance Score Calculation
ChromaDB returns cosine distance $d \in [0, 2]$. `RAGRetriever` converts cosine distance to a deterministic relevance score $R \in [0.0, 1.0]$:

$$R = \max\left(0.0, \min\left(1.0, 1.0 - \frac{d}{2.0}\right)\right)$$

* Distance $d = 0.0 \implies R = 1.0$ (Exact match)
* Distance $d = 1.0 \implies R = 0.5$ (Orthogonal)
* Distance $d \ge 2.0 \implies R = 0.0$ (Opposite)

Relevance scores represent mathematical vector closeness, **NOT** factual confidence or truth assertions.

### 4.3 Minimum Relevance Filtering
Candidate chunks with $R < \text{min\_relevance}$ are filtered out of the result set.

### 4.4 Metadata Filtering
Submits optional ChromaDB `where` metadata filters (e.g. `{"document_type": "MARKDOWN"}` or `{"filename": "vessel_feasibility_rules.md"}`) to restrict search scope to specific stages, sources, or documents.

### 4.5 Deterministic Result Ordering
Retrieved chunks are ordered deterministically:
1. Primary sort: **Highest relevance score descending**
2. Secondary sort (tie-breaker): **Chunk ID ascending (`chunk_id`)**

---

## 5. Provenance Preservation

Every `RetrievedChunk` preserves complete lineage metadata from Stage 7.2 ingestion:

* `document_id`: Parent document hash
* `chunk_id`: Unique chunk identifier
* `filename`: Source file basename
* `source`: Provenance source attribution (`INTERNAL`)
* `stage`: Stage attribution (`Stage 7.2` / `Stage 7.3`)
* `document_type`: File format (`MARKDOWN` / `TEXT`)
* `checksum`: Raw SHA-256 file content hash digest
* `chunk_index`: Position in document chunk sequence
* `embedding_model`: Model identifier string
* `embedding_dimension`: Vector dimension integer

---

## 6. No-Result Handling & Status Codes

`RAGRetriever` returns explicit status codes and empty result lists rather than fabricating answers:

* `SUCCESS`: At least 1 evidence chunk satisfied all query filters and relevance thresholds.
* `NO_RELEVANT_EVIDENCE`: Vector search completed, but 0 chunks met the minimum relevance threshold (`min_relevance`).
* `EMPTY_COLLECTION`: Target ChromaDB vector store collection contains 0 indexed chunks.

---

## 7. Safety, Security, and Boundary Rules

1. **No LLM Generation**: Does not invoke LLM inference engines or construct prompt completions.
2. **No Numerical Alteration**: Does not alter Stage 2 freight forecasts, Stage 3 delay scores, Stage 4 feasibility flags, Stage 5 costs, or Stage 6 optimization results.
3. **No File Exfiltration**: Accesses strictly indexed approved documents in ChromaDB. Does not load `.env`, credentials, source code, or binary files.
4. **No Fabricated Evidence**: Returned `text` fields contain exact, unedited snippets from indexed documents.

---

## 8. Verification and Test Suite

Stage 7.3 is verified via `tests/test_stage7_3_rag_retrieval.py` covering:

1. Empty query rejection (`ValueError`)
2. Whitespace query rejection (`ValueError`)
3. Invalid `top_k` rejection (`ValueError`)
4. `RetrievalQuery` serialization/deserialization
5. `RetrievalResult` serialization/deserialization
6. Top-K limit compliance
7. Metadata preservation in retrieved chunks
8. Full provenance tracking preservation
9. Deterministic result ordering
10. Relevance threshold filtering (`min_relevance`)
11. Empty collection handling (`EMPTY_COLLECTION`)
12. Zero matching chunk handling (`NO_RELEVANT_EVIDENCE`)
13. Metadata filter matching (`where` clause)
14. Embedding model metadata preservation
15. Incompatible embedding configuration rejection
16. Deterministic test retrieval using `DeterministicLocalEmbeddingModel`
17. Source document immutability verification
18. Core Stage 2-6 output immutability verification
19. Zero fabricated evidence assertion

---

## 9. Limitations & Stage 7.4 Roadmap

### Limitations
* Stage 7.3 retrieves document evidence; it does **NOT** synthesize summaries or answer natural language questions.
* Similarity search depends on vector proximity; semantic intent mapping will be refined by LLM agents in Stage 7.4.

### Next Steps (Stage 7.4)
* **Stage 7.4 (LLM Agent & RAG Synthesis)**: Integrates `RAGRetriever` into Stage 7.1 AI Agents (`LLMExplanationAgent`, `QAAgent`) to generate evidence-backed, safety-validated explanations of FreightWise decisions.
