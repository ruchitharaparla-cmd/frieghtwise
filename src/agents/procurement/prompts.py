"""Stage 7.6 System Prompt and Prompt Builder for Procurement Strategy Agent."""

import json
from typing import List, Optional

from src.agents.contracts import AgentContext, EvidenceItem
from src.agents.procurement.contracts import ProcurementAnalysisRequest

PROCUREMENT_STRATEGY_SYSTEM_PROMPT = """You are the FreightWise Procurement Strategy Agent, a charter procurement and optimizer allocation explanation layer.

CRITICAL ARCHITECTURAL RULES & SAFETY BOUNDARIES:
1. Authoritative Procurement Inputs: Stage 5 voyage charter cost outputs and Stage 6 CP-SAT optimization solver outputs are authoritative.
2. No Cost or Allocation Mutation: NEVER recalculate, override, or fabricate voyage charter costs, fuel calculations, or solver allocation quantities.
3. No Solver Plan Overrides: NEVER propose or mandate a vessel allocation plan that conflicts with or overrides Stage 6 CP-SAT outputs.
4. Scope & Feasibility Preservation: Obey all Stage 4 feasibility flags and Stage 3 risk scores. Never assign numerical values to DATA_UNAVAILABLE.
5. Explanatory Strategy Role: Your recommendations must explain pre-computed scenario trade-offs and summarize CP-SAT solver selections.
6. Citation Integrity: Do not fabricate citations or evidence IDs. Reference only provided evidence IDs.
"""


def build_procurement_analysis_prompt(
    request: ProcurementAnalysisRequest,
    context: Optional[AgentContext] = None,
    evidence: Optional[List[EvidenceItem]] = None,
) -> str:
    """Build structured user prompt string for the Procurement Strategy Agent."""
    prompt_lines: List[str] = [
        "=== FREIGHTWISE PROCUREMENT STRATEGY REQUEST ===",
        f"USER QUESTION: {request.question.strip()}",
        "",
        "=== AUTHORITATIVE PIPELINE CONTEXT (STAGES 2-6) ===",
    ]

    if context:
        ctx_dict = context.to_dict()
        has_data = False
        for k in ["freight_forecast", "cost_result", "optimization_result", "feasibility_result"]:
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
    prompt_lines.append("Explain the procurement strategy using the authoritative pipeline context and retrieved evidence. Obey all safety rules.")

    return "\n".join(prompt_lines)
