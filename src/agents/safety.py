"""
Safety validation rules and enforcement helpers for FreightWise Stage 7 AI Agents + RAG layer.

Critical Architectural Rule:
LLMs must NEVER make numerical decisions.
The authoritative numerical/decision pipeline is:
Stage 1 Data Foundation -> Stage 2 Freight Forecasting -> Stage 3 Delay/Congestion
-> Stage 4 Feasibility -> Stage 5 Cost/Risk -> Stage 6 Optimization -> Optimal Plan

LLM agents may ONLY:
- retrieve evidence
- summarize
- explain
- compare already-computed alternatives
- identify documented risks
- answer questions using retrieved evidence
- explain why the optimizer selected a plan

LLM agents must NOT:
- change freight forecasts
- calculate or override costs
- override feasibility
- invent vessel capacity / availability
- invent port LOA/beam/draft constraints
- invent Indian port congestion
- invent bunker/insurance/port charges
- modify Stage 6 optimization results
- turn DATA_UNAVAILABLE into a numerical value
- present GLOBAL_CONGESTION_PROXY as Indian-specific congestion
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional

from src.agents.contracts import AgentContext, AgentResponse, EvidenceItem, ProvenanceRecord


@dataclass
class SafetyCheckResult:
    """Result container for safety validation checks."""
    is_valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_violation(self, msg: str):
        self.is_valid = False
        self.violations.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class AgentSafetyError(Exception):
    """Exception raised when an agent safety rule is violated."""
    pass


def verify_authoritative_immutability(
    original_context: AgentContext,
    modified_context: AgentContext,
) -> SafetyCheckResult:
    """
    Verify that authoritative numerical values from Stage 2-6 pipeline outputs
    in original_context have not been altered or modified in modified_context.
    """
    result = SafetyCheckResult(is_valid=True)
    stages = [
        ("freight_forecast", original_context.freight_forecast, modified_context.freight_forecast),
        ("delay_prediction", original_context.delay_prediction, modified_context.delay_prediction),
        ("congestion_prediction", original_context.congestion_prediction, modified_context.congestion_prediction),
        ("feasibility_result", original_context.feasibility_result, modified_context.feasibility_result),
        ("cost_result", original_context.cost_result, modified_context.cost_result),
        ("optimization_result", original_context.optimization_result, modified_context.optimization_result),
    ]

    for stage_name, orig, mod in stages:
        if orig is None and mod is not None:
            result.add_violation(f"Authoritative field '{stage_name}' was fabricated (was None in original context).")
        elif orig is not None and mod is None:
            result.add_violation(f"Authoritative field '{stage_name}' was cleared or removed in modified context.")
        elif orig is not None and mod is not None:
            _compare_dicts(stage_name, orig, mod, result)

    return result


def _compare_dicts(prefix: str, orig: Dict[str, Any], mod: Dict[str, Any], result: SafetyCheckResult):
    """Recursive comparison helper for numerical immutability checking."""
    for key, orig_val in orig.items():
        if key not in mod:
            result.add_violation(f"Key '{prefix}.{key}' missing in modified context.")
            continue
        mod_val = mod[key]

        if isinstance(orig_val, dict) and isinstance(mod_val, dict):
            _compare_dicts(f"{prefix}.{key}", orig_val, mod_val, result)
        elif isinstance(orig_val, (int, float)) and isinstance(mod_val, (int, float)):
            if abs(orig_val - mod_val) > 1e-6:
                result.add_violation(
                    f"Authoritative numerical value '{prefix}.{key}' modified from {orig_val} to {mod_val}."
                )
        elif orig_val != mod_val:
            result.add_violation(
                f"Authoritative attribute '{prefix}.{key}' modified from '{orig_val}' to '{mod_val}'."
            )


def verify_data_scope(
    claimed_scope: str,
    context: Optional[AgentContext] = None,
) -> SafetyCheckResult:
    """
    Verify that data scope claims respect FreightWise boundaries.
    In particular, GLOBAL_CONGESTION_PROXY must NEVER be claimed as verified Indian port congestion.
    """
    result = SafetyCheckResult(is_valid=True)
    forbidden_claims = [
        "VERIFIED_INDIAN_PORT_CONGESTION",
        "INDIAN_PORT_SPECIFIC_CONGESTION",
        "INDIAN_PORT_CONGESTION_DATASET",
    ]
    if claimed_scope.upper() in forbidden_claims:
        result.add_violation(
            f"Scope claim '{claimed_scope}' is forbidden. GLOBAL_CONGESTION_PROXY cannot be represented as verified Indian port congestion."
        )

    if context and context.congestion_prediction:
        actual_scope = context.congestion_prediction.get("data_scope", "")
        if actual_scope == "GLOBAL_CONGESTION_PROXY" and "INDIAN" in claimed_scope.upper():
            result.add_violation(
                f"Cannot represent data scope '{actual_scope}' as Indian-specific congestion claim '{claimed_scope}'."
            )

    return result


def verify_data_unavailability(
    context: AgentContext,
    target_dict: Optional[Dict[str, Any]] = None,
) -> SafetyCheckResult:
    """
    Verify that DATA_UNAVAILABLE statuses in Stage 4/6 remain preserved and are not turned into numerical values.
    """
    result = SafetyCheckResult(is_valid=True)

    # Check feasibility result
    if context.feasibility_result:
        status = context.feasibility_result.get("status") or context.feasibility_result.get("feasibility_status")
        if status == "DATA_UNAVAILABLE":
            # Ensure numerical outputs were not generated for this candidate
            if context.feasibility_result.get("evaluated_numerical_capacity") is not None:
                result.add_violation("DATA_UNAVAILABLE candidate cannot have fabricated numerical capacity.")

    # Check target_dict if provided
    if target_dict:
        for k, v in target_dict.items():
            if v == "DATA_UNAVAILABLE":
                # Ensure no accompanying numerical override
                num_key = f"{k}_value"
                if target_dict.get(num_key) is not None:
                    result.add_violation(f"DATA_UNAVAILABLE field '{k}' converted to numerical value {target_dict.get(num_key)}.")

    return result


def validate_agent_response(
    response: AgentResponse,
    context: Optional[AgentContext] = None,
) -> SafetyCheckResult:
    """
    Comprehensive safety validator inspecting AgentResponse for:
    - Fabricated numerical values or modified authoritative outputs
    - Unsupported Indian port congestion claims
    - Treating GLOBAL_CONGESTION_PROXY as India-specific
    - Overriding DATA_UNAVAILABLE
    - Unsupported vessel physical constraints (vessel LOA, beam, draft, verified DWT)
    - Unsupported cost components (bunker, insurance, port charges)
    """
    result = SafetyCheckResult(is_valid=True)
    text = response.answer or ""

    # 1. Check for unsupported Indian port congestion claims
    if re.search(r"\b(verified|actual|measured)\s+Indian\s+port\s+congestion\b", text, re.IGNORECASE) or \
       re.search(r"\bIndian\s+port\s+congestion\s+index\b", text, re.IGNORECASE):
        result.add_violation(
            "Forbidden claim: Global congestion predictions are a GLOBAL_CONGESTION_PROXY and must NEVER be presented as verified Indian port congestion."
        )

    # 2. Check for unsupported vessel physical constraints inventions
    if re.search(r"\bverified\s+vessel\s+(dwt|capacity|loa|beam|draft)\b", text, re.IGNORECASE) or \
       re.search(r"\b(actual|specific)\s+vessel\s+imo\b", text, re.IGNORECASE) or \
       re.search(r"\bphysical\s+vessel\s+dimensions\s+override\b", text, re.IGNORECASE):
        result.add_violation(
            "Forbidden claim: Individual vessel DWT/LOA/beam/draft data is unavailable in baseline datasets and must not be fabricated."
        )

    # 3. Check for unsupported cost components inventions
    if re.search(r"\b(calculated|override|invented)\s+(bunker|insurance|port\s+charges|canal\s+fee)\b", text, re.IGNORECASE) or \
       re.search(r"\bcustom\s+bunker\s+surcharge\s+usd\b", text, re.IGNORECASE):
        result.add_violation(
            "Forbidden claim: LLM agents must not calculate, fabricate, or override cost components (bunker, insurance, port charges)."
        )

    # 4. Check for overriding DATA_UNAVAILABLE into numerical numbers
    if re.search(r"\bconverted\s+DATA_UNAVAILABLE\s+to\b", text, re.IGNORECASE) or \
       re.search(r"\bDATA_UNAVAILABLE\s+numerical\s+value\b", text, re.IGNORECASE):
        result.add_violation(
            "Forbidden claim: DATA_UNAVAILABLE status cannot be converted to a numerical value."
        )

    # 5. Check for freight forecast override claims
    if re.search(r"\b(adjusted|modified|recalculated|overrode)\s+freight\s+forecast\b", text, re.IGNORECASE) or \
       re.search(r"\bnew\s+freight\s+rate\s+prediction\b", text, re.IGNORECASE):
        result.add_violation(
            "Forbidden claim: LLM agents must not modify or recalculate Stage 2 freight forecasts."
        )

    # 6. Check context immutability if context is present
    if context:
        unavail_res = verify_data_unavailability(context)
        if not unavail_res.is_valid:
            for v in unavail_res.violations:
                result.add_violation(v)

    return result
