# FreightWise Stage 7.4 - Market Analyst Agent Layer Architecture

## 1. System Overview & Purpose

FreightWise Stage 7.4 implements the **Market Analyst Agent Layer** (`src/agents/market/service.py`, `agent.py`, `contracts.py`, `prompts.py`). Stage 7.4 connects the existing FreightWise Stage 7.1 safety/context foundation and Stage 7.3 RAG retrieval service to an LLM-based Market Analyst Agent.

> [!IMPORTANT]
> **"The Market Analyst Agent is an explanation and evidence-synthesis layer. It is not the numerical decision engine."**

Stage 7.4 does **NOT** implement:
* Risk Agent
* Procurement Agent
* CrewAI
* Multi-agent orchestration
* Autonomous decision making

```
Stage 2 Freight Forecasting (XGBoost / LightGBM)
Stage 3 Delay & Congestion Prediction
Stage 4 Feasibility Rules
Stage 5 Voyage Charter Cost Engine
Stage 6 Optimization Engine (CP-SAT Solver)
                    |
                    v
          Stage 7.1 AgentContext
                    |
          +---------+---------+
          |                   |
          v                   v
Stage 7.3 RAG           Authoritative
  Retriever           numerical outputs
          |                   |
          +---------+---------+
                    |
                    v
          Market Analyst Agent
     (Explanation & Synthesis Layer)
                    |
                    v
        Structured Response & Findings
```

---

## 2. Market Agent Contracts (`src/agents/market/contracts.py`)

### 2.1 MarketAnalysisRequest
Input request contract sent to `MarketAnalystService`:

| Field Name | Type | Default | Description |
| --- | --- | --- | --- |
| `question` | `str` | *Required* | User or system query string (non-empty) |
| `context` | `Optional[AgentContext]` | `None` | Bound Stage 7.1 authoritative context |
| `retrieval_query` | `Optional[str]` | `None` | Custom search query for RAG retrieval |
| `max_evidence_items` | `int` | `5` | Maximum number of RAG evidence items |
| `include_limitations` | `bool` | `True` | Include boundary limitations disclaimers |
| `metadata` | `Dict[str, Any]` | `{}` | Additional query metadata |

### 2.2 MarketFinding
Individual analytical finding linked strictly to pipeline data or RAG evidence:

| Field Name | Type | Description |
| --- | --- | --- |
| `finding` | `str` | Textual analytical finding statement |
| `basis` | `str` | Origin (`AUTHORITATIVE_PIPELINE`, `RETRIEVED_EVIDENCE`, `ANALYTICAL_INTERPRETATION`) |
| `evidence_ids` | `List[str]` | List of evidence IDs referencing Stage 7.3 evidence chunks |
| `numerical_reference` | `Optional[str]` | Citation string of authoritative numerical output |
| `confidence_label` | `str` | Confidence tag (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `DATA_LIMITED`) |

> [!NOTE]
> `confidence_label` must **NOT** be represented as statistical model confidence unless provided by underlying models. Allowed values are strictly `SUPPORTED`, `PARTIALLY_SUPPORTED`, or `DATA_LIMITED`.

### 2.3 MarketAnalysisResponse
Structured response payload returned by `MarketAnalystService`:

| Field Name | Type | Description |
| --- | --- | --- |
| `request_id` | `str` | Unique request UUID |
| `answer` | `str` | Main explanation text string |
| `key_findings` | `List[MarketFinding]` | List of evidence-backed findings |
| `evidence` | `List[EvidenceItem]` | Complete list of attached RAG evidence items |
| `numerical_inputs` | `Dict[str, Any]` | Authoritative Stage 2-6 numerical summary dict |
| `limitations` | `List[str]` | Boundary and scope limitation statements |
| `warnings` | `List[str]` | Validation warnings or safety flags |
| `provenance` | `Optional[ProvenanceRecord]` | Lineage tracking metadata record |
| `model_name` | `str` | Identifier of model provider used |
| `model_version` | `str` | Provider version string |
| `response_status` | `str` | Status (`SUCCESS`, `VALIDATION_FAILED`, `PROVIDER_UNAVAILABLE`) |

---

## 3. System Prompt & Prompt Engineering (`src/agents/market/prompts.py`)

`MARKET_ANALYST_SYSTEM_PROMPT` explicitly enforces 14 mandatory safety rules:

1. **Authoritative Pipeline Output**: Stage 2-6 numerical outputs are authoritative.
2. **No Recalculation or Modification**: Never recalculate or alter Stage 2-6 numbers.
3. **No Numerical Invention**: Never invent missing numerical values, freight rates, or costs.
4. **Scope Boundaries**: `GLOBAL_CONGESTION_PROXY` must NEVER be claimed as verified Indian port congestion.
5. **Preserve Data Unavailability**: `DATA_UNAVAILABLE` must remain `DATA_UNAVAILABLE`.
6. **Evidence Priority**: Retrieved document chunks provide explanation, NOT authority over numbers.
7. **Conflict Resolution**: Explain evidence conflicts rather than changing numerical outputs.
8. **Attribution Clarity**: Distinguish facts, model outputs, evidence, assumptions, and limitations.
9. **No Fabricated Vessel Specs**: Do not invent individual vessel DWT, LOA, beam, draft, or IMO numbers.
10. **No Fabricated Port Specs**: Do not invent port depth or infrastructure restrictions.
11. **Optimizer Alignment**: Do not claim an optimization plan recommendation not present in Stage 6.
12. **No Forecast Generation**: Do not create numerical forecasts yourself.
13. **No Procurement Decisions**: Do not make charter procurement decisions.
14. **Citation Integrity**: Do not fabricate citations or evidence IDs.

---

## 4. Provider Abstraction (`src/agents/market/agent.py`)

Stage 7.4 defines a pluggable model interface `BaseMarketAnalystModel`:

* **`OpenAIMarketAnalystModel` (Production Provider)**:
  Pluggable provider for production LLM generation (default: `gpt-4o-mini`).
  * If `OPENAI_API_KEY` or the `openai` package is missing, returns an explicit `PROVIDER_UNAVAILABLE` response status.
  * **SAFEGUARD**: Never silently falls back to test models in production.
* **`DeterministicTestMarketAnalystModel` (Test-Only Provider)**:
  Offline, deterministic provider used **STRICTLY FOR UNIT TESTS**.
  * Extracts Stage 2-6 numbers and RAG evidence IDs without calling external APIs.
  * **SAFEGUARD**: Restricted to unit test suites and offline test fixtures.

---

## 5. RAG Retrieval Integration (`src/agents/market/service.py`)

`MarketAnalystService` integrates Stage 7.3 `RAGRetriever`:

1. Queries Stage 7.3 RAG knowledge base for user search query.
2. Converts retrieved `RetrievedChunk` instances into Stage 7.1 `EvidenceItem` objects.
3. Preserves all chunk provenance metadata (`chunk_id`, `document_id`, `filename`, `source`, `stage`, `document_type`, `checksum`, `chunk_index`, `embedding_model`, `embedding_dimension`).
4. Ensures evidence IDs referenced in `MarketFinding` instances point ONLY to evidence actually returned by Stage 7.3.
5. Does NOT read arbitrary local filesystem files directly; consumes evidence strictly through RAG.

---

## 6. Authoritative Numerical Pipeline & Safety Boundaries

### 6.1 Authoritative Numerical Immutability
The service makes isolated deep copies of `AgentContext` and numerical dicts. The LLM is never allowed to modify numerical values.
* If forecast rate is `28500.0 USD/day`, response may state "28,500 USD/day", but cannot change it to "29,000 USD/day".
* If a status is `DATA_UNAVAILABLE`, it remains `DATA_UNAVAILABLE`.

### 6.2 Stage 7.1 Safety Validation
Every generated response passes through Stage 7.1 safety checks:
* `validate_agent_response()`: Rejects fabricated vessel/port specs, custom bunker surcharges, freight forecast overrides, or Indian congestion claims for `GLOBAL_CONGESTION_PROXY`.
* `verify_authoritative_immutability()`: Flags any numerical modification as a safety violation.

If safety checks fail, the service sets `response_status = "VALIDATION_FAILED"` and records explicit violation messages in `warnings`.

---

## 7. Verification and Testing

Stage 7.4 is fully verified via `tests/test_stage7_4_market_agent.py` covering 24 test scenarios:

1. Valid `MarketAnalysisRequest` validation
2. Empty question rejection
3. Request serialization/deserialization
4. Response serialization/deserialization
5. `MarketFinding` serialization and confidence label validation
6. Provider interface compliance
7. Provider-unavailable status handling
8. Deterministic test provider execution
9. Stage 7.3 RAG retrieval integration
10. Evidence item preservation
11. Provenance record preservation
12. Authoritative numerical values preservation
13. `DATA_UNAVAILABLE` status preservation
14. `GLOBAL_CONGESTION_PROXY` scope boundary check
15. Rejection of fabricated vessel physical specifications
16. Rejection of fabricated port infrastructure constraints
17. Rejection of fabricated numerical costs
18. Immutability of Stage 6 optimizer outputs
19. Immutability of caller `AgentContext`
20. Immutability of retrieved evidence items
21. Citation integrity (zero fabricated evidence IDs)
22. Limitation disclaimer handling
23. Complete end-to-end `MarketAnalystService` execution flow
24. Stage 1-6 regression compatibility

---

## 8. Multi-Agent Roadmap

Stage 7.4 establishes the Market Analyst Agent as a standalone explanation service.

* **Future (Stage 7.5)**: Risk Analyst Agent & Procurement Strategy Agent.
* **Future (Stage 7.6)**: Multi-Agent Orchestration & Consensus Verification.
