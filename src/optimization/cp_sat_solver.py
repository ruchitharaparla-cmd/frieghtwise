"""
Google OR-Tools CP-SAT Solver wrapper and Solution Pool Generator for Stage 6 Engine.

Executes deterministic integer optimization, parses solver solutions into structured
OptimizationPlan objects, and extracts alternative feasible plans via exclusion constraints.

Solver Modes
------------
LEXICOGRAPHIC (solve_hierarchical=True — default):
    Genuine 4-priority hierarchical optimisation executed as three sequential
    CP-SAT solve calls, each fixing the preceding priority's optimal value as
    a hard constraint.

    Phase 1 — Hard feasibility:
        Structurally enforced.  Only Stage 4 FEASIBLE candidates enter the
        executable pool (handled by CandidateBuilder before this solver is called).

    Phase 2 — Demand fulfilment:
        Minimise total commodity shortage (MT).
        Optimal shortage S* is recorded and fixed as per-commodity hard
        constraints before Phase 3.

    Phase 3 — Economic delivered cost:
        Minimise total delivered voyage cost (USD) subject to shortage <= S*.
        Optimal cost C* is recorded and fixed as a hard upper-bound constraint
        before Phase 4.

    Phase 4 — Risk / delay minimisation:
        Minimise total delay and commercial risk penalties (USD-normalised)
        subject to shortage <= S* and cost <= C*.

WEIGHTED (solve_hierarchical=False):
    Single-pass USD-normalised weighted scalar objective.
    This mode is NOT lexicographic; it is retained for legacy compatibility.
"""

from typing import List, Dict, Any, Optional, Tuple
import time
from ortools.sat.python import cp_model

from src.optimization.contracts import (
    EnrichedCandidate,
    OptimizationRequest,
    OptimizationPlan,
    VoyageAllocation,
    OptimizationStatus,
    PlanType,
)
from src.optimization.constraints import OptimizationConstraintBuilder
from src.optimization.objective import OptimizationObjectiveBuilder


class CPSatOptimizationSolver:
    """Wrapper around Google OR-Tools CP-SAT solver."""

    def __init__(
        self,
        constraint_builder: Optional[OptimizationConstraintBuilder] = None,
        objective_builder: Optional[OptimizationObjectiveBuilder] = None,
    ):
        self.constraint_builder = constraint_builder or OptimizationConstraintBuilder()
        self.objective_builder = objective_builder or OptimizationObjectiveBuilder()

    # ------------------------------------------------------------------
    # Public dispatcher
    # ------------------------------------------------------------------

    def solve(
        self,
        candidates: List[EnrichedCandidate],
        request: OptimizationRequest,
        max_time_seconds: float = 10.0,
        extract_alternatives: bool = True,
    ) -> Tuple[str, Optional[OptimizationPlan], List[OptimizationPlan], float]:
        """
        Solves the CP-SAT optimization model.

        Dispatches to:
          - ``solve_lexicographic`` when ``request.solve_hierarchical is True`` (default).
          - ``solve_weighted``      when ``request.solve_hierarchical is False``.

        Returns:
            - solver_status: str (OPTIMAL | FEASIBLE | INFEASIBLE | ERROR)
            - primary_plan: Optional[OptimizationPlan]
            - alternative_plans: List[OptimizationPlan]
            - execution_time_seconds: float
        """
        if request.solve_hierarchical:
            return self.solve_lexicographic(
                candidates=candidates,
                request=request,
                max_time_seconds=max_time_seconds,
            )
        return self.solve_weighted(
            candidates=candidates,
            request=request,
            max_time_seconds=max_time_seconds,
            extract_alternatives=extract_alternatives,
        )

    # ------------------------------------------------------------------
    # LEXICOGRAPHIC solver (solve_hierarchical=True)
    # ------------------------------------------------------------------

    def solve_lexicographic(
        self,
        candidates: List[EnrichedCandidate],
        request: OptimizationRequest,
        max_time_seconds: float = 10.0,
    ) -> Tuple[str, Optional[OptimizationPlan], List[OptimizationPlan], float]:
        """
        Genuine 4-priority hierarchical/lexicographic optimisation.

        The four priorities are optimised in strict sequential order.  Each
        phase fixes the preceding phase's optimal value as a hard constraint
        before the next objective is introduced.

        Priority 1 — hard feasibility:
            Structural: only FEASIBLE candidates are passed to this solver.

        Priority 2 — demand fulfilment:
            Minimise total shortage (MT) → record S* per commodity.

        Priority 3 — economic delivered cost:
            Minimise sum(x_i * delivered_cost_i) subject to shortage = S*.
            Record optimal cost C*.

        Priority 4 — risk / delay:
            Minimise delay + risk penalties subject to shortage = S* AND cost <= C*.
        """
        start_time = time.time()

        if not candidates:
            return OptimizationStatus.INFEASIBLE.value, None, [], time.time() - start_time

        # ----------------------------------------------------------------
        # Phase 2: Minimise total commodity shortage (demand fulfilment)
        # ----------------------------------------------------------------
        model_p2 = cp_model.CpModel()
        x_p2, q_p2, shortage_p2 = self.constraint_builder.build_variables_and_constraints(
            model_p2, candidates, request
        )
        self.objective_builder.build_phase2_shortage_objective(model_p2, shortage_p2)

        solver_p2 = cp_model.CpSolver()
        solver_p2.parameters.max_time_in_seconds = max_time_seconds / 3.0
        solver_p2.parameters.random_seed = 42
        status_p2 = solver_p2.Solve(model_p2)

        if status_p2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_str = (
                OptimizationStatus.INFEASIBLE.value
                if status_p2 == cp_model.INFEASIBLE
                else OptimizationStatus.ERROR.value
            )
            return status_str, None, [], time.time() - start_time

        # Record per-commodity optimal shortage values (S*)
        optimal_shortage_per_commodity: Dict[str, int] = {
            comm: int(solver_p2.Value(sv)) for comm, sv in shortage_p2.items()
        }
        p2_total_shortage_tons = sum(optimal_shortage_per_commodity.values())

        # ----------------------------------------------------------------
        # Phase 3: Minimise economic delivered cost, shortage fixed at S*
        # ----------------------------------------------------------------
        model_p3 = cp_model.CpModel()
        x_p3, q_p3, shortage_p3 = self.constraint_builder.build_variables_and_constraints(
            model_p3, candidates, request
        )

        # Fix each commodity shortage to its Phase 2 optimal value (hard constraint)
        for comm, opt_shortage in optimal_shortage_per_commodity.items():
            if comm in shortage_p3:
                model_p3.Add(shortage_p3[comm] == opt_shortage)

        cost_expr_p3 = self.objective_builder.build_phase3_cost_expression(candidates, x_p3)
        model_p3.Minimize(sum(cost_expr_p3) if cost_expr_p3 else 0)

        solver_p3 = cp_model.CpSolver()
        solver_p3.parameters.max_time_in_seconds = max_time_seconds / 3.0
        solver_p3.parameters.random_seed = 43
        status_p3 = solver_p3.Solve(model_p3)

        if status_p3 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Phase 3 failed — fall back to Phase 2 solution
            is_optimal = status_p2 == cp_model.OPTIMAL
            plan = self._extract_plan(
                solver=solver_p2,
                candidates=candidates,
                x_vars=x_p2,
                q_vars=q_p2,
                plan_id="PRIMARY_EXECUTABLE_PLAN_1",
                plan_type=PlanType.EXECUTABLE_OPTIMAL.value,
                is_primary_optimal=is_optimal,
                objective_mode="LEXICOGRAPHIC",
                lexico_achieved={
                    "p2_shortage_tons": p2_total_shortage_tons,
                    "p3_economic_cost_usd": None,
                    "p4_risk_penalty_usd": None,
                    "note": "Phase 3 (cost) infeasible; plan reflects Phase 2 only.",
                },
            )
            return (
                OptimizationStatus.FEASIBLE.value,
                plan,
                [],
                time.time() - start_time,
            )

        p3_optimal_cost_int = int(round(solver_p3.ObjectiveValue()))

        # ----------------------------------------------------------------
        # Phase 4: Minimise risk/delay, shortage and cost fixed
        # ----------------------------------------------------------------
        model_p4 = cp_model.CpModel()
        x_p4, q_p4, shortage_p4 = self.constraint_builder.build_variables_and_constraints(
            model_p4, candidates, request
        )

        # Fix shortage (S*)
        for comm, opt_shortage in optimal_shortage_per_commodity.items():
            if comm in shortage_p4:
                model_p4.Add(shortage_p4[comm] == opt_shortage)

        # Fix economic cost (C*) — allow at-or-below the optimal
        cost_expr_p4 = self.objective_builder.build_phase3_cost_expression(candidates, x_p4)
        if cost_expr_p4:
            model_p4.Add(sum(cost_expr_p4) <= p3_optimal_cost_int)

        self.objective_builder.build_phase4_risk_objective(
            model_p4, candidates, x_p4, request.weights
        )

        solver_p4 = cp_model.CpSolver()
        solver_p4.parameters.max_time_in_seconds = max_time_seconds / 3.0
        solver_p4.parameters.random_seed = 44
        status_p4 = solver_p4.Solve(model_p4)

        exec_time = time.time() - start_time

        if status_p4 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Phase 4 failed — use Phase 3 solution as the final plan
            is_optimal = status_p3 == cp_model.OPTIMAL
            plan = self._extract_plan(
                solver=solver_p3,
                candidates=candidates,
                x_vars=x_p3,
                q_vars=q_p3,
                plan_id="PRIMARY_EXECUTABLE_PLAN_1",
                plan_type=PlanType.EXECUTABLE_OPTIMAL.value,
                is_primary_optimal=is_optimal,
                objective_mode="LEXICOGRAPHIC",
                lexico_achieved={
                    "p2_shortage_tons": p2_total_shortage_tons,
                    "p3_economic_cost_usd": p3_optimal_cost_int,
                    "p4_risk_penalty_usd": None,
                    "note": "Phase 4 (risk) infeasible; plan reflects Phases 2+3.",
                },
            )
            return OptimizationStatus.FEASIBLE.value, plan, [], exec_time

        p4_optimal_risk_int = int(round(solver_p4.ObjectiveValue()))
        is_optimal = status_p4 == cp_model.OPTIMAL

        lexico_achieved = {
            "p2_shortage_tons": p2_total_shortage_tons,
            "p3_economic_cost_usd": p3_optimal_cost_int,
            "p4_risk_penalty_usd": p4_optimal_risk_int,
        }

        primary_plan = self._extract_plan(
            solver=solver_p4,
            candidates=candidates,
            x_vars=x_p4,
            q_vars=q_p4,
            plan_id="PRIMARY_EXECUTABLE_PLAN_1",
            plan_type=PlanType.EXECUTABLE_OPTIMAL.value,
            is_primary_optimal=is_optimal,
            objective_mode="LEXICOGRAPHIC",
            lexico_achieved=lexico_achieved,
        )

        status_str = (
            OptimizationStatus.OPTIMAL.value if is_optimal else OptimizationStatus.FEASIBLE.value
        )
        return status_str, primary_plan, [], exec_time

    # ------------------------------------------------------------------
    # WEIGHTED solver (solve_hierarchical=False) — NOT lexicographic
    # ------------------------------------------------------------------

    def solve_weighted(
        self,
        candidates: List[EnrichedCandidate],
        request: OptimizationRequest,
        max_time_seconds: float = 10.0,
        extract_alternatives: bool = True,
    ) -> Tuple[str, Optional[OptimizationPlan], List[OptimizationPlan], float]:
        """
        WEIGHTED SCALAR solver (single-pass, NOT lexicographic).

        Combines all objectives into one USD-normalised weighted expression.
        This mode is NOT equivalent to the lexicographic solver; it may trade
        demand fulfilment against economic cost depending on penalty weights.

        Retained for legacy compatibility and comparative analysis.
        """
        start_time = time.time()

        if not candidates:
            return OptimizationStatus.INFEASIBLE.value, None, [], time.time() - start_time

        model = cp_model.CpModel()
        x_vars, q_vars, shortage_vars = self.constraint_builder.build_variables_and_constraints(
            model, candidates, request
        )
        self.objective_builder.build_weighted_objective(
            model, candidates, x_vars, q_vars, shortage_vars, request
        )

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_time_seconds
        solver.parameters.random_seed = 42

        status_code = solver.Solve(model)
        exec_time = time.time() - start_time

        if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_str = (
                OptimizationStatus.INFEASIBLE.value
                if status_code == cp_model.INFEASIBLE
                else OptimizationStatus.ERROR.value
            )
            return status_str, None, [], exec_time

        is_optimal = status_code == cp_model.OPTIMAL
        primary_status_str = (
            OptimizationStatus.OPTIMAL.value if is_optimal else OptimizationStatus.FEASIBLE.value
        )

        primary_plan = self._extract_plan(
            solver=solver,
            candidates=candidates,
            x_vars=x_vars,
            q_vars=q_vars,
            plan_id="PRIMARY_EXECUTABLE_PLAN_1",
            plan_type=PlanType.EXECUTABLE_OPTIMAL.value,
            is_primary_optimal=is_optimal,
            objective_mode="WEIGHTED",
            lexico_achieved=None,
        )

        alternative_plans: List[OptimizationPlan] = []

        if extract_alternatives and primary_plan and primary_plan.allocations:
            # Solution Pool extraction via exclusion constraints
            alt_count = 1
            current_model = model
            selected_indices = [
                idx for idx, x_var in x_vars.items() if solver.Value(x_var) == 1
            ]

            while alt_count <= 2 and selected_indices:
                current_model.Add(
                    sum(x_vars[idx] for idx in selected_indices) <= len(selected_indices) - 1
                )

                alt_solver = cp_model.CpSolver()
                alt_solver.parameters.max_time_in_seconds = max_time_seconds / 2.0
                alt_solver.parameters.random_seed = 42 + alt_count

                alt_status = alt_solver.Solve(current_model)
                if alt_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    alt_plan = self._extract_plan(
                        solver=alt_solver,
                        candidates=candidates,
                        x_vars=x_vars,
                        q_vars=q_vars,
                        plan_id=f"ALTERNATIVE_EXECUTABLE_PLAN_{alt_count + 1}",
                        plan_type=PlanType.EXECUTABLE_ALTERNATIVE.value,
                        is_primary_optimal=False,
                        objective_mode="WEIGHTED",
                        lexico_achieved=None,
                    )
                    if alt_plan and alt_plan.allocations:
                        alternative_plans.append(alt_plan)
                        selected_indices = [
                            idx for idx, x_var in x_vars.items()
                            if alt_solver.Value(x_var) == 1
                        ]
                        alt_count += 1
                    else:
                        break
                else:
                    break

        return primary_status_str, primary_plan, alternative_plans, exec_time

    # ------------------------------------------------------------------
    # Plan extraction helper
    # ------------------------------------------------------------------

    def _extract_plan(
        self,
        solver: cp_model.CpSolver,
        candidates: List[EnrichedCandidate],
        x_vars: Dict[int, cp_model.IntVar],
        q_vars: Dict[int, cp_model.IntVar],
        plan_id: str,
        plan_type: str,
        is_primary_optimal: bool,
        objective_mode: str = "WEIGHTED",
        lexico_achieved: Optional[Dict[str, Any]] = None,
    ) -> OptimizationPlan:
        """Helper to extract an OptimizationPlan from solver values."""
        allocations: List[VoyageAllocation] = []
        total_cost = 0.0
        total_cargo_tons = 0
        total_delay_hours = 0.0
        risk_scores: List[float] = []

        alloc_counter = 1
        for idx, cand in enumerate(candidates):
            if solver.Value(x_vars[idx]) == 1:
                qty_tons = int(solver.Value(q_vars[idx]))
                if qty_tons > 0:
                    voyage_days = 10.0
                    deliv_cost = cand.voyage_cost_usd + (cand.forecast_freight_usd_day * voyage_days)

                    alloc = VoyageAllocation(
                        allocation_id=f"ALLOC_{alloc_counter:03d}",
                        period=cand.candidate.period,
                        forecast_date=cand.candidate.forecast_date,
                        origin=cand.candidate.origin,
                        destination_port=cand.candidate.destination_port,
                        commodity=cand.candidate.commodity,
                        cargo_quantity_tons=qty_tons,
                        vessel_archetype=cand.vessel_archetype,
                        forecast_freight_usd_day=cand.forecast_freight_usd_day,
                        voyage_cost_usd=cand.voyage_cost_usd,
                        turnaround_hours=cand.turnaround_hours,
                        delay_risk_score=cand.delay_risk_score,
                        congestion_proxy_score=cand.congestion_proxy_score,
                        congestion_data_scope=cand.congestion_data_scope,
                        stage4_status=cand.stage4_status,
                    )
                    allocations.append(alloc)
                    total_cost += deliv_cost
                    total_cargo_tons += qty_tons
                    total_delay_hours += cand.turnaround_hours
                    risk_scores.append(cand.delay_risk_score)
                    alloc_counter += 1

        avg_risk = float(sum(risk_scores) / len(risk_scores)) if risk_scores else 0.0
        obj_val = float(solver.ObjectiveValue())

        return OptimizationPlan(
            plan_id=plan_id,
            plan_type=plan_type,
            is_primary_optimal=is_primary_optimal,
            objective_value=obj_val,
            total_cost_usd=total_cost,
            total_cargo_tons=total_cargo_tons,
            expected_delay_hours=total_delay_hours,
            average_risk_score=avg_risk,
            allocations=allocations,
            objective_mode=objective_mode,
            lexicographic_achieved_values=lexico_achieved,
        )
