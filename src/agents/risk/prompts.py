"""Stage 7.5 System Prompt and Prompt Builder for Risk Agent Layer."""

import json
from typing import List, Optional

from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.risk.contracts import RiskAnalysisRequest

RISK_ANALYST_SYSTEM_PROMPT = """You are the FreightWise Risk Analyst Agent, an operational risk interpretation and delay evaluation layer.

CRITICAL ARCHITECTURAL RULES & SAFETY BOUNDARIES:
1. Authoritative Risk Pipeline: Stage 3 delay/congestion predictions and Stage 5 risk scores are authoritative.
2. No Risk Recalculation: NEVER recalculate, override, or fabricate turnaround delay hours or congestion indices.
3. No Custom Cost Surcharges: NEVER invent custom demurrage, insurance penalties, or bunker surcharges.
4. Scope Boundaries: GLOBAL_CONGESTION_PROXY is a global proxy and must NEVER be claimed as verified Indian port congestion.
5. Preserve Data Unavailability: DATA_UNAVAILABLE statuses must remain DATA_UNAVAILABLE. Do not assign estimated numbers to unverified risks.
6. Evidence Linking: Reference retrieved document evidence IDs for factual basis. Do not fabricate citations.
7. Explanatory Scope: Distinguish between model-predicted risk scores, retrieved document evidence, and analytical limitations.
"""


def build_risk_analysis_prompt(
    request: RiskAnalysisRequest,
    context: Optional[AgentContext] = None,
    evidence: Optional[List[EvidenceItem]] = None,
) -> str:
    """Build structured user prompt string for the Risk Analyst Agent."""
    prompt_lines: List[str] = [
        "=== FREIGHTWISE RISK ANALYSIS REQUEST ===",
        f"USER QUESTION: {request.question.strip()}",
        "",
        "=== AUTHORITATIVE PIPELINE CONTEXT (STAGES 2-6) ===",
    ]

    if context:
        ctx_dict = context.to_dict()
        has_data = False
        for k in ["delay_prediction", "congestion_prediction", "feasibility_result", "cost_result", "optimization_result"]:
            val = ctx_dict.get(k)
            if val is not None:
                has_data = True
                prompt_lines.append(f"[{k.upper()}]: {json.dumps(val)}")
        if not has_data:
            prompt_lines.append("NO_PIPELINE_OUTPUTS_PROVIDED")
    else:
        prompt_lines.append("NO_PIPELINE_OUTPUTS_PROVIDED")

    prompt_lines.append("")
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
    prompt_lines.append("Analyze the risk question using the authoritative pipeline context and retrieved evidence. Obey all safety rules.")

    return "\n".join(prompt_lines)
