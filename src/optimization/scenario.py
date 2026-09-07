"""
Scenario Analysis & Sensitivity Evaluation Engine for Stage 6.

Evaluates plan robustness across market scenarios:
- BASE: Unmodified baseline inputs
- HIGH_FREIGHT: +25% freight rate increase
- HIGH_DELAY: +40% turnaround delay increase
- DATA_UNAVAILABLE_EXPLORATORY: Sensitivity run including unverified candidates
  (Strictly labeled EXPLORATORY_SENSITIVITY_PLAN, never Executable Optimal Plan)
"""

from typing import List, Dict, Any, Optional
import copy

from src.optimization.contracts import (
    OptimizationRequest,
    OptimizationPlan,
    EnrichedCandidate,
    PlanType,
)
from src.optimization.candidate_builder import CandidateBuilder, CandidateBuildResult
from src.optimization.cp_sat_solver import CPSatOptimizationSolver


class ScenarioEvaluator:
    """Evaluates multi-scenario sensitivity and exploratory runs."""

    def __init__(
        self,
        candidate_builder: Optional[CandidateBuilder] = None,
        solver: Optional[CPSatOptimizationSolver] = None,
    ):
        self.candidate_builder = candidate_builder or CandidateBuilder()
        self.solver = solver or CPSatOptimizationSolver()

    def evaluate_scenarios(
        self, request: OptimizationRequest, build_result: CandidateBuildResult
    ) -> Dict[str, OptimizationPlan]:
        """
        Executes scenario evaluations for BASE, HIGH_FREIGHT, HIGH_DELAY,
        and optionally DATA_UNAVAILABLE_EXPLORATORY scenarios.
        """
        scenario_results: Dict[str, OptimizationPlan] = {}

        # 1. BASE Scenario (FEASIBLE candidates)
        status_base, plan_base, _, _ = self.solver.solve(
            candidates=build_result.executable_candidates,
            request=request,
            extract_alternatives=False,
        )
        if plan_base:
            plan_base.plan_id = "SCENARIO_BASE_PLAN"
            scenario_results["BASE"] = plan_base

        # 2. HIGH_FREIGHT Scenario (+25% freight rates)
        high_freight_cands = copy.deepcopy(build_result.executable_candidates)
        for cand in high_freight_cands:
            cand.forecast_freight_usd_day *= 1.25

        _, plan_freight, _, _ = self.solver.solve(
            candidates=high_freight_cands,
            request=request,
            extract_alternatives=False,
        )
        if plan_freight:
            plan_freight.plan_id = "SCENARIO_HIGH_FREIGHT_PLAN"
            scenario_results["HIGH_FREIGHT"] = plan_freight

        # 3. HIGH_DELAY Scenario (+40% turnaround delay)
        high_delay_cands = copy.deepcopy(build_result.executable_candidates)
        for cand in high_delay_cands:
            cand.turnaround_hours *= 1.40
            cand.delay_risk_score = min(100.0, cand.delay_risk_score * 1.40)

        _, plan_delay, _, _ = self.solver.solve(
            candidates=high_delay_cands,
            request=request,
            extract_alternatives=False,
        )
        if plan_delay:
            plan_delay.plan_id = "SCENARIO_HIGH_DELAY_PLAN"
            scenario_results["HIGH_DELAY"] = plan_delay

        # 4. DATA_UNAVAILABLE_EXPLORATORY Scenario (Includes unverified candidates)
        if request.include_exploratory_scenario:
            # Combine FEASIBLE + DATA_UNAVAILABLE candidates for exploratory sensitivity
            exploratory_cands: List[EnrichedCandidate] = []
            for cand in build_result.all_enriched_candidates:
                if cand.stage4_status in ("FEASIBLE", "DATA_UNAVAILABLE"):
                    # Deepcopy and mark status as FEASIBLE for exploratory solver pass
                    e_cand = copy.deepcopy(cand)
                    exploratory_cands.append(e_cand)

            if exploratory_cands:
                _, plan_exp, _, _ = self.solver.solve(
                    candidates=exploratory_cands,
                    request=request,
                    extract_alternatives=False,
                )
                if plan_exp:
                    plan_exp.plan_id = "SCENARIO_EXPLORATORY_PLAN"
                    # Strictly label as EXPLORATORY_SENSITIVITY_PLAN, never Executable
                    plan_exp.plan_type = PlanType.EXPLORATORY_SENSITIVITY.value
                    plan_exp.is_primary_optimal = False
                    scenario_results["DATA_UNAVAILABLE_EXPLORATORY"] = plan_exp

        return scenario_results
