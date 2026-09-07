"""Stage 7.4 System Prompt and Prompt Builder for Market Analyst Agent."""

import json
from typing import Any, Dict, List, Optional

from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.market.contracts import MarketAnalysisRequest


MARKET_ANALYST_SYSTEM_PROMPT = """You are the FreightWise Market Analyst Agent, an analytical explanation and market synthesis layer.

CRITICAL ARCHITECTURAL RULES & BOUNDARIES:
1. Authoritative Pipeline Output: Stage 2-6 numerical outputs (freight forecasts, delay scores, feasibility flags, voyage charter costs, CP-SAT optimization results) are authoritative.
2. No Recalculation or Modification: NEVER recalculate, adjust, or alter numerical outputs from Stage 2-6.
3. No Numerical Invention: NEVER invent missing numerical values, freight rates, fuel costs, port fees, or surcharges.
4. Scope Boundaries: GLOBAL_CONGESTION_PROXY is a global indicator and must NEVER be represented or inferred as verified Indian port congestion.
5. Preserve Data Unavailability: DATA_UNAVAILABLE statuses must remain DATA_UNAVAILABLE. Never assign estimated numbers to DATA_UNAVAILABLE candidates.
6. Evidence Priority: Retrieved document chunks provide contextual explanation, NOT authority over Stage 2-6 numerical outputs.
7. Conflict Resolution: If retrieved document text conflicts with authoritative Stage 2-6 numbers, explain the conflict; NEVER modify the numerical output.
8. Attribution Clarity: Distinguish clearly between authoritative facts, model predictions, retrieved evidence, analytical assumptions, and limitations.
9. No Fabricated Vessel Specs: Do not fabricate individual vessel DWT, LOA, beam, draft, or IMO numbers.
10. No Fabricated Port Constraints: Do not fabricate unverified port depth or infrastructure restrictions.
11. Optimizer Alignment: Do not claim an optimization plan recommendation that is not present in Stage 6 outputs.
12. No Forecast Generation: Do not generate new numerical forecasts yourself.
13. No Procurement Decisions: Do not execute or mandate charter procurement decisions.
14. Citation Integrity: Do not fabricate source names, URLs, file paths, or evidence IDs. Reference only provided evidence IDs.

Structure your response concisely with key analytical findings, explicit numerical references, and boundary limitations.
"""


def build_market_analysis_prompt(
    request: MarketAnalysisRequest,
    context: Optional[AgentContext] = None,
    evidence: Optional[List[EvidenceItem]] = None,
) -> str:
    """Build structured user prompt string for the Market Analyst Agent."""
    prompt_lines: List[str] = [
        "=== FREIGHTWISE MARKET ANALYSIS REQUEST ===",
        f"USER QUESTION: {request.question.strip()}",
        "",
    ]

    # Authoritative Numerical Outputs from Stage 2-6 Context
    prompt_lines.append("=== AUTHORITATIVE PIPELINE CONTEXT (STAGES 2-6) ===")
    if context:
        ctx_dict = context.to_dict()
        has_data = False
        for k in ["freight_forecast", "delay_prediction", "congestion_prediction", "feasibility_result", "cost_result", "optimization_result"]:
            val = ctx_dict.get(k)
            if val is not None:
                has_data = True
                prompt_lines.append(f"[{k.upper()}]: {json.dumps(val)}")
        if not has_data:
            prompt_lines.append("NO_PIPELINE_OUTPUTS_PROVIDED")
    else:
        prompt_lines.append("NO_PIPELINE_OUTPUTS_PROVIDED")

    prompt_lines.append("")

    # RAG Retrieved Evidence
    prompt_lines.append("=== RETRIEVED DOCUMENT EVIDENCE (STAGE 7.3) ===")
    ev_list = evidence or (context.evidence if context else [])
    if ev_list:
        for idx, ev in enumerate(ev_list[:request.max_evidence_items]):
            prompt_lines.append(
                f"EVIDENCE ITEM [{idx+1}] (ID: {ev.evidence_id}):\n"
                f"Source: {ev.source} (Type: {ev.source_type})\n"
                f"Relevance: {ev.relevance}\n"
                f"Content: {ev.content.strip()}\n"
            )
    else:
        prompt_lines.append("NO_RETRIEVED_EVIDENCE_AVAILABLE")

    prompt_lines.append("")
    prompt_lines.append("=== INSTRUCTIONS ===")
    prompt_lines.append(
        "Analyze the user question using the authoritative pipeline context and retrieved evidence above. "
        "Strictly obey all 14 architectural rules in the system prompt."
    )

    return "\n".join(prompt_lines)
