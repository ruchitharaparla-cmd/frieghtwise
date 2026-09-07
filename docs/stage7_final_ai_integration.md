# FreightWise Stage 7 Final AI Integration - Technical Documentation
# Stages 7.5 to 7.8: Risk Agent, Procurement Agent, Multi-Agent Orchestrator, End-to-End Service

## 1. Purpose and Scope

Stages 7.5 through 7.8 complete the FreightWise Stage 7 AI/RAG layer by implementing:

- Stage 7.5: Risk Analyst Agent - interprets Stage 3 delay and Stage 5 risk outputs
- Stage 7.6: Procurement Strategy Agent - explains Stage 5/6 charter and optimization decisions
- Stage 7.7: Multi-Agent Orchestrator - dispatches queries to all agents and synthesizes combined responses
- Stage 7.8: End-to-End AI/RAG Integration Service (FreightWiseAIService) - unified entry point

These stages operate strictly DOWNSTREAM of the FreightWise authoritative numerical pipeline
(Stages 1-6). The AI layer provides natural-language explanation, evidence synthesis, and
strategy commentary. It NEVER makes freight predictions, calculates costs, overrides
feasibility decisions, or mutates Stage 6 CP-SAT solver outputs.

---

## 2. Architecture

```
User Query + Stage 2-6 Outputs
        |
        v
  FreightWiseAIService.query_ai_assistant()   [Stage 7.8]
        |
        v
  build_agent_context()                        [Stage 7.1]
  (Binds Stage 2-6 outputs into AgentContext)
        |
        v
  MultiAgentOrchestrator.orchestrate()         [Stage 7.7]
        |
   +----+----+----+
   |         |         |
   v         v         v
MarketAnalyst  RiskAnalyst  ProcurementStrategy
Service        Service      Service
[Stage 7.4]   [Stage 7.5]  [Stage 7.6]
   |              |              |
   v              v              v
RAGRetriever  RAGRetriever  RAGRetriever  [Stage 7.3 each]
   |              |              |
ChromaDB      ChromaDB      ChromaDB     [Stage 7.2 knowledge base]
   |              |              |
   +----+----+----+
        |
        v
  Deduplicate evidence
  Synthesize narrative answer
  Extract and validate findings (real evidence IDs only)
  Determine overall status
        |
        v
  MultiAgentOrchestrationResponse
        |
        v
  FreightWiseAIServiceResponse
```

---

## 3. Stage 7.5 - Risk Analyst Agent

### Purpose

Interprets authoritative Stage 3 delay predictions and Stage 5 risk scores as operational
risk commentary. Does NOT recalculate risk scores or override delay predictions.

### Files

- `src/agents/risk/__init__.py` - Package exports
- `src/agents/risk/contracts.py` - Data contracts
- `src/agents/risk/prompts.py` - LLM system prompt with safety rules
- `src/agents/risk/agent.py` - Provider abstraction and model implementations
- `src/agents/risk/service.py` - Service orchestrator

### Contracts

#### RiskAnalysisRequest

```python
@dataclass
class RiskAnalysisRequest:
    question: str                          # Required, non-empty
    context: Optional[AgentContext]        # Authoritative Stage 2-6 context
    retrieval_query: Optional[str]         # Override for RAG query
    max_evidence_items: int = 5
    include_limitations: bool = True
    metadata: Dict[str, Any]
```

#### RiskFinding

```python
@dataclass
class RiskFinding:
    finding: str
    risk_category: str  # 'TURNAROUND_DELAY', 'PORT_CONGESTION', 'VOYAGE_RISK', 'DATA_UNAVAILABLE_RISK'
    evidence_ids: List[str]
    numerical_reference: Optional[str]
    confidence_label: str  # 'SUPPORTED', 'PARTIALLY_SUPPORTED', 'DATA_LIMITED'
```

#### RiskAnalysisResponse

```python
@dataclass
class RiskAnalysisResponse:
    request_id: str
    answer: str
    risk_findings: List[RiskFinding]
    evidence: List[EvidenceItem]
    numerical_inputs: Dict[str, Any]   # Read-only copy of Stage 2-6 values
    limitations: List[str]
    warnings: List[str]
    provenance: Optional[ProvenanceRecord]
    model_name: str
    model_version: str
    response_status: str  # 'SUCCESS', 'VALIDATION_FAILED', 'PROVIDER_UNAVAILABLE'
```

### Provider Abstraction

- `BaseRiskAnalystModel` - Abstract base class (all providers must implement)
- `OpenAIRiskAnalystModel` - Production provider using OpenAI API
- `DeterministicTestRiskAnalystModel` - TEST-ONLY deterministic model for offline unit tests
- `get_risk_analyst_model(is_testing=False)` - Factory function

> **IMPORTANT**: DeterministicTestRiskAnalystModel is TEST-ONLY. It must NEVER be used
> in production. If is_testing=False and OpenAI API key is missing, the service returns
> response_status='PROVIDER_UNAVAILABLE'. There is NO silent fallback to fake data.

### Safety Rules Enforced by Risk Agent

1. Stage 3 delay predictions are authoritative and immutable.
2. Stage 5 risk scores are authoritative and immutable.
3. GLOBAL_CONGESTION_PROXY scope cannot be claimed as verified Indian port congestion.
4. DATA_UNAVAILABLE values are preserved exactly.
5. No numerical risk score recalculations permitted.
6. No vessel or port specifications may be invented.

---

## 4. Stage 7.6 - Procurement Strategy Agent

### Purpose

Explains Stage 5 charter cost calculations and Stage 6 CP-SAT solver vessel allocation
decisions as strategy commentary. Does NOT override charter rates or CP-SAT selections.

### Files

- `src/agents/procurement/__init__.py` - Package exports
- `src/agents/procurement/contracts.py` - Data contracts
- `src/agents/procurement/prompts.py` - LLM system prompt with safety rules
- `src/agents/procurement/agent.py` - Provider abstraction and model implementations
- `src/agents/procurement/service.py` - Service orchestrator

### Contracts

#### ProcurementAnalysisRequest

```python
@dataclass
class ProcurementAnalysisRequest:
    question: str
    context: Optional[AgentContext]
    retrieval_query: Optional[str]
    max_evidence_items: int = 5
    include_limitations: bool = True
    metadata: Dict[str, Any]
```

#### ProcurementRecommendation

```python
@dataclass
class ProcurementRecommendation:
    recommendation: str
    strategy_category: str  # 'CHARTER_STRATEGY', 'OPTIMIZER_PLAN_EXPLANATION', 'SCENARIO_COMPARISON'
    evidence_ids: List[str]
    numerical_reference: Optional[str]
    confidence_label: str  # 'SUPPORTED', 'PARTIALLY_SUPPORTED', 'DATA_LIMITED'
```

#### ProcurementAnalysisResponse

```python
@dataclass
class ProcurementAnalysisResponse:
    request_id: str
    answer: str
    recommendations: List[ProcurementRecommendation]
    evidence: List[EvidenceItem]
    numerical_inputs: Dict[str, Any]
    limitations: List[str]
    warnings: List[str]
    provenance: Optional[ProvenanceRecord]
    model_name: str
    model_version: str
    response_status: str  # 'SUCCESS', 'VALIDATION_FAILED', 'PROVIDER_UNAVAILABLE'
```

### Provider Abstraction

- `BaseProcurementModel` - Abstract base class
- `OpenAIProcurementModel` - Production provider using OpenAI API
- `DeterministicTestProcurementModel` - TEST-ONLY deterministic model for offline unit tests
- `get_procurement_model(is_testing=False)` - Factory function

> **IMPORTANT**: DeterministicTestProcurementModel is TEST-ONLY. Production mode returns
> PROVIDER_UNAVAILABLE if OpenAI key is missing. No silent fallback.

### Safety Rules Enforced by Procurement Agent

1. Stage 5 charter costs are authoritative and immutable.
2. Stage 6 CP-SAT solver selections are authoritative and immutable.
3. No charter rate overrides permitted.
4. No vessel allocation changes permitted.
5. No fabrication of vessel specs or port constraints.
6. DATA_UNAVAILABLE values preserved exactly.

---

## 5. Stage 7.7 - Multi-Agent Orchestrator

### Purpose

Dispatches queries to Market Analyst (Stage 7.4), Risk Analyst (Stage 7.5), and
Procurement Strategy (Stage 7.6) agents. Synthesizes combined responses, deduplicates
evidence, and enforces safety contracts across all outputs.

### Files

- `src/agents/orchestrator/__init__.py` - Package exports
- `src/agents/orchestrator/contracts.py` - Data contracts
- `src/agents/orchestrator/service.py` - Orchestrator implementation

### Contracts

#### MultiAgentOrchestrationRequest

```python
@dataclass
class MultiAgentOrchestrationRequest:
    question: str
    context: Optional[AgentContext]
    retrieval_query: Optional[str]    # Override for RAG retrieval query
    max_evidence_items: int = 5
    enable_market: bool = True
    enable_risk: bool = True
    enable_procurement: bool = True
    metadata: Dict[str, Any]
```

Validation: question must be non-empty; at least one agent must be enabled.

#### AgentSynthesisFinding

```python
@dataclass
class AgentSynthesisFinding:
    agent_source: str   # 'MARKET', 'RISK', 'PROCUREMENT'
    finding: str
    confidence_label: str
    evidence_ids: List[str]  # Must reference only real combined_evidence IDs
```

#### MultiAgentOrchestrationResponse

```python
@dataclass
class MultiAgentOrchestrationResponse:
    request_id: str
    synthesized_answer: str             # Narrative only, no numerical decisions
    market_response: Optional[MarketAnalysisResponse]
    risk_response: Optional[RiskAnalysisResponse]
    procurement_response: Optional[ProcurementAnalysisResponse]
    combined_evidence: List[EvidenceItem]   # Deduplicated from all agents
    key_findings: List[AgentSynthesisFinding]
    limitations: List[str]
    warnings: List[str]
    response_status: str
    # 'SUCCESS', 'PARTIAL_SUCCESS', 'ALL_PROVIDERS_UNAVAILABLE', 'VALIDATION_FAILED'
```

### Orchestration Process

1. Validate request (non-empty question, at least one agent enabled).
2. Deep copy AgentContext to prevent mutation.
3. Dispatch enabled agents sequentially:
   - MarketAnalystService.analyze() if enable_market
   - RiskAnalystService.analyze() if enable_risk
   - ProcurementStrategyService.analyze() if enable_procurement
4. Collect per-agent responses and evidence lists.
5. Deduplicate combined evidence by evidence_id.
6. Synthesize narrative answer from successful agent answers (no numerical decisions).
7. Extract key findings, filtering evidence_ids to only real combined_evidence IDs.
8. Determine overall status.
9. Return MultiAgentOrchestrationResponse.

### Overall Status Rules

| Condition | Status |
|---|---|
| All enabled agents return SUCCESS | SUCCESS |
| All enabled agents return PROVIDER_UNAVAILABLE | ALL_PROVIDERS_UNAVAILABLE |
| Any agent returns VALIDATION_FAILED | VALIDATION_FAILED |
| Mixed SUCCESS and PROVIDER_UNAVAILABLE | PARTIAL_SUCCESS |

### Standard Limitations (always included)

- "Multi-Agent Orchestrator is an explanatory and analytical layer only."
- "No numerical decisions or predictions are made by the AI layer."
- "All freight rates, delay times, risk scores, and optimization results are authoritative Stage 2-6 outputs."
- "GLOBAL_CONGESTION_PROXY is a global indicator and cannot be claimed as verified Indian port congestion."
- "DATA_UNAVAILABLE values are preserved; agents do not fabricate missing data."

---

## 6. Stage 7.8 - FreightWiseAIService (End-to-End Integration)

### Purpose

Provides the unified, high-level entry point for all FreightWise AI capabilities.
Accepts Stage 2-6 outputs or a pre-built AgentContext, binds them into context,
dispatches to the Multi-Agent Orchestrator, and returns a structured response.

### File

- `src/agents/service.py`

### Usage

```python
from src.agents.service import FreightWiseAIService

# Initialize (use is_testing=True for offline tests)
ai_service = FreightWiseAIService(is_testing=False)  # production

# Execute an AI-assisted query
response = ai_service.query_ai_assistant(
    query="What are the primary risks for this voyage?",
    stage2_output=my_forecast_result,     # Stage 2 freight forecast
    stage3_output=my_delay_result,         # Stage 3 delay/congestion prediction
    stage4_output=my_feasibility_result,   # Stage 4 feasibility evaluation
    stage5_output=my_cost_result,          # Stage 5 cost/risk calculation
    stage6_output=my_optimization_result,  # Stage 6 CP-SAT optimization
    enable_market=True,
    enable_risk=True,
    enable_procurement=True,
)

print(response.synthesized_answer)
print(response.status)
print(response.pipeline_context_summary)
```

### FreightWiseAIServiceResponse

```python
@dataclass
class FreightWiseAIServiceResponse:
    service_id: str                                    # Unique request ID
    query: str                                         # Original query
    orchestration_response: MultiAgentOrchestrationResponse
    synthesized_answer: str                            # Narrative synthesis
    status: str                                        # Overall status
    timestamp: str                                     # UTC timestamp
    pipeline_context_summary: Dict[str, Any]           # Read-only Stage 2-6 summary
    metadata: Dict[str, Any]
```

### query_ai_assistant() Parameters

| Parameter | Type | Description |
|---|---|---|
| query | str | User question (required, non-empty) |
| stage2_output | Any | Stage 2 freight forecasting output |
| stage3_output | Any | Stage 3 delay/congestion prediction |
| stage4_output | Any | Stage 4 feasibility evaluation |
| stage5_output | Any | Stage 5 cost/risk evaluation |
| stage6_output | Any | Stage 6 CP-SAT optimization output |
| context | AgentContext | Pre-built context (overrides stage2_6 if provided) |
| enable_market | bool | Enable Market Analyst Agent (default: True) |
| enable_risk | bool | Enable Risk Analyst Agent (default: True) |
| enable_procurement | bool | Enable Procurement Strategy Agent (default: True) |
| retrieval_query | str | Override RAG retrieval query (default: query) |
| max_evidence_items | int | Max evidence items per agent (default: 5) |
| metadata | Dict | Extra metadata for response |

---

## 7. Safety Contracts (Non-Negotiable)

All of Stages 7.5-7.8 must satisfy these safety contracts inherited from Stage 7.1:

### 7.1 Downstream-Only Operation

The AI layer is DOWNSTREAM of Stage 2-6. It receives outputs; it does NOT produce them.

### 7.2 Numerical Immutability

- Freight rates (Stage 2) are immutable.
- Delay predictions and congestion indices (Stage 3) are immutable.
- Feasibility status (Stage 4) is immutable.
- Charter costs and risk premiums (Stage 5) are immutable.
- CP-SAT optimization selections (Stage 6) are immutable.

### 7.3 DATA_UNAVAILABLE Preservation

If a Stage 2-6 output is None or marked DATA_UNAVAILABLE, agents must preserve this.
Agents MUST NOT substitute a default value or fabricate a placeholder.

### 7.4 GLOBAL_CONGESTION_PROXY Scope Boundary

Stage 3 port congestion prediction uses a global AIS-based proxy and is NOT verified
Indian subcontinent port congestion data. Agents must not reinterpret the scope.

### 7.5 No Silent Fallback

If a production LLM provider is unavailable (API key missing, network error):
- The per-agent response_status is 'PROVIDER_UNAVAILABLE'.
- The orchestrator propagates this in MultiAgentOrchestrationResponse.response_status.
- FreightWiseAIServiceResponse.status reflects the unavailability.
- DeterministicTestRiskAnalystModel / DeterministicTestProcurementModel are NOT activated
  silently in production.

### 7.6 Evidence ID Validity

Evidence IDs in key_findings and agent findings must reference only real EvidenceItem
objects present in the combined_evidence or individual agent evidence lists.
Fabricated source names, URLs, or citation IDs are prohibited.

---

## 8. Provider Configuration

### OpenAI (Production Default)

Set the OPENAI_API_KEY environment variable:

```
OPENAI_API_KEY=sk-...
```

The Market, Risk, and Procurement agents will automatically use OpenAI as the production
LLM provider. The model defaults to gpt-4o-mini but is configurable.

### Testing (Offline Mode)

```python
service = FreightWiseAIService(is_testing=True)
```

When is_testing=True, all three agents use their respective DeterministicTest*Model
implementations. These are offline, deterministic, and require no API key.
They are NOT suitable for production use.

---

## 9. Testing

### Run Stage 7 Final Integration Tests

```
python -m pytest tests/test_stage7_final_integration.py -v
```

### Run All Stage 7 Tests

```
python -m pytest tests/test_stage7_*.py -v
```

### Run Full Regression Suite

```
python tests/run_tests.py
```

### Test Coverage Categories

1. Risk Agent request/response contracts
2. Risk Agent provider abstraction and safety enforcement
3. Procurement Agent contracts and prompt rules
4. Procurement Agent provider abstraction and safety enforcement
5. Multi-Agent Orchestrator dispatch and synthesis
6. End-to-End FreightWiseAIService execution flow
7. RAG evidence integration and provenance tracking across all agents
8. Preservation of authoritative Stage 2-6 numerical outputs
9. Preservation of DATA_UNAVAILABLE across all agents
10. Preservation of GLOBAL_CONGESTION_PROXY scope boundaries
11. Rejection of fabricated vessel/port specs and cost surcharges
12. Immutability of Stage 6 CP-SAT solver selections
13. Zero regression across Stages 1-6

---

## 10. Limitations

1. The AI layer produces explanatory narratives and commentary only. It does not replace
   the authoritative numerical decision outputs from Stages 2-6.

2. Market, Risk, and Procurement agents are dispatched sequentially in the current
   implementation. Parallel dispatch may be added in future iterations for performance.

3. RAG retrieval quality depends on the documents ingested into the Stage 7.2 ChromaDB
   knowledge base. If the knowledge base is empty, agents receive no RAG evidence and
   rely entirely on the Stage 2-6 context.

4. GLOBAL_CONGESTION_PROXY is derived from global AIS/port data. It is NOT
   a verified Indian East Coast congestion signal.

5. The synthesized_answer is a concatenation of individual agent answers with source
   attribution. Semantic cross-agent synthesis requires a dedicated Stage 7.9 reasoning
   layer (future work).

---

## 11. SIH Demonstration Guide

To demonstrate the full Stage 7 AI stack for the Smart India Hackathon:

```python
from src.agents.service import FreightWiseAIService

# Initialize in offline testing mode (no API key needed)
service = FreightWiseAIService(is_testing=True)

# Simulate authoritative Stage 2-6 outputs
stage2 = {"predicted_freight_rate": 45000.0, "unit": "USD/day", "model_name": "CatBoost"}
stage3 = {"predicted_delay_hours": 12.5, "delay_risk_score": 0.42, "data_scope": "EAST_COAST_INDIA",
           "predicted_congestion_index": 0.71, "data_scope": "GLOBAL_CONGESTION_PROXY"}
stage4 = {"feasibility_status": "FEASIBLE", "vessel_id": "V001"}
stage5 = {"charter_cost_usd": 315000.0, "voyage_risk_premium": 12000.0}
stage6 = {"optimization_status": "OPTIMAL", "selected_vessel_id": "V001", "total_cost_usd": 327000.0}

# Execute multi-agent AI query
response = service.query_ai_assistant(
    query="What are the key risks and market conditions for this voyage?",
    stage2_output=stage2,
    stage3_output=stage3,
    stage4_output=stage4,
    stage5_output=stage5,
    stage6_output=stage6,
)

print("Status:", response.status)
print("Query:", response.query)
print()
print("=== AI Synthesis ===")
print(response.synthesized_answer)
print()
print("=== Pipeline Context Summary ===")
for k, v in response.pipeline_context_summary.items():
    print(f"  {k}: {v}")
```

---

## 12. Future Integration Points

- Stage 7.9: Cross-agent reasoning layer that semantically integrates Market, Risk,
  and Procurement outputs into a single coherent advisory narrative.
- Parallel agent dispatch for reduced latency.
- Additional LLM providers (Anthropic Claude, Google Gemini, local Ollama).
- Streaming response support for interactive UI integration.
- Feedback loop integration for agent output quality tracking.
