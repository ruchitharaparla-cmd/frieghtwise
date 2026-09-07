"""
Objective function builders for Google OR-Tools CP-SAT model in Stage 6.

Two distinct solver modes are provided:

LEXICOGRAPHIC (hierarchical) mode — ``solve_hierarchical=True``
    Optimises the four priorities in strict sequential order.
    Each phase fixes the preceding phase's optimal value as a hard constraint
    before optimising the next.  This is a genuine lexicographic formulation.

    Priority 1 (hard feasibility)
        Enforced structurally: only Stage 4 FEASIBLE candidates enter the
        executable candidate pool.  No objective expression is needed.

    Priority 2 (demand fulfilment)
        Minimise total commodity shortage (tons).
        Constraint: total_procured + shortage >= target  (from constraints.py)
        Objective:  Minimise sum(shortage_vars)

    Priority 3 (economic delivered cost)
        Minimise total delivered voyage cost (USD).
        Phase 2 optimal shortage is fixed as a hard per-commodity constraint.
        Objective:  Minimise sum(x_i * delivered_cost_i)

    Priority 4 (risk / delay minimisation)
        Minimise total delay and commercial risk penalties (USD-normalised).
        Phase 3 optimal cost is fixed as a hard constraint.
        Objective:  Minimise sum(x_i * (delay_penalty + risk_penalty + congestion_penalty))

WEIGHTED (scalar) mode — ``solve_hierarchical=False``
    Single-pass USD-normalised minimisation combining all objectives into one
    scalar expression with configurable penalty weights.
    This mode is retained for legacy compatibility.
    It is NOT lexicographic or hierarchical and must NOT be described as such.
"""

from typing import List, Dict, Any, Tuple, Optional
from ortools.sat.python import cp_model

from src.optimization.contracts import EnrichedCandidate, OptimizationRequest


class OptimizationObjectiveBuilder:
    """Builds CP-SAT objective terms for economic cost, delays, risks, and shortage penalties."""

    # ------------------------------------------------------------------
    # Shared cost component calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_candidate_cost_components(
        cand: EnrichedCandidate,
    ) -> Tuple[int, int, int, int]:
        """
        Calculates integer USD component terms for a candidate:
        - Delivered Cost (Base Voyage Cost + Forecast Freight Rate for ~10 day voyage)
        - Delay Cost (Turnaround hours scaled by delay_cost_per_hour_usd weight)
        - Risk Cost (Delay risk score + Commercial risk score scaled)
        - Congestion Proxy Cost (Global proxy index scaled)

        All values are integer USD so they are valid CP-SAT objective coefficients.
        """
        # Benchmark estimated voyage duration: 10 days for handysize bulk route
        voyage_days = 10.0
        freight_component_usd = cand.forecast_freight_usd_day * voyage_days
        delivered_cost_usd = int(round(cand.voyage_cost_usd + freight_component_usd))

        turnaround_hours_int = int(round(cand.turnaround_hours))
        delay_risk_points = int(round(cand.delay_risk_score + cand.commercial_risk_score * 100.0))
        congestion_proxy_int = int(round(cand.congestion_proxy_score * 10.0))  # Scaled ×10 for precision

        return delivered_cost_usd, turnaround_hours_int, delay_risk_points, congestion_proxy_int

    # ------------------------------------------------------------------
    # Phase-specific objective builders for LEXICOGRAPHIC mode
    # ------------------------------------------------------------------

    def build_phase2_shortage_objective(
        self,
        model: cp_model.CpModel,
        shortage_vars: Dict[str, cp_model.IntVar],
    ) -> None:
        """
        Phase 2 (Priority 2): Minimise total commodity shortage (MT).
        Maximises demand fulfilment lexicographically before any cost optimisation.
        """
        if shortage_vars:
            model.Minimize(sum(shortage_vars.values()))
        else:
            # No demand targets: shortage is trivially zero; nothing to minimise.
            model.Minimize(0)

    def build_phase3_cost_objective(
        self,
        model: cp_model.CpModel,
        candidates: List[EnrichedCandidate],
        x_vars: Dict[int, cp_model.IntVar],
    ) -> int:
        """
        Phase 3 (Priority 3): Minimise total economic delivered cost (USD).
        Returns the objective expression sum for use as a hard constraint in Phase 4.

        The returned integer is the *coefficient sum* — the actual achieved value
        is read from solver.ObjectiveValue() after solving.
        """
        cost_expr = []
        for idx, cand in enumerate(candidates):
            delivered_cost_usd, _, _, _ = self.calculate_candidate_cost_components(cand)
            cost_expr.append(x_vars[idx] * delivered_cost_usd)

        model.Minimize(sum(cost_expr) if cost_expr else 0)
        return sum(c.constant if hasattr(c, "constant") else 0 for c in cost_expr)

    def build_phase3_cost_expression(
        self,
        candidates: List[EnrichedCandidate],
        x_vars: Dict[int, cp_model.IntVar],
    ) -> list:
        """Returns the list of cost expression terms (for adding as a hard constraint)."""
        cost_expr = []
        for idx, cand in enumerate(candidates):
            delivered_cost_usd, _, _, _ = self.calculate_candidate_cost_components(cand)
            cost_expr.append(x_vars[idx] * delivered_cost_usd)
        return cost_expr

    def build_phase4_risk_objective(
        self,
        model: cp_model.CpModel,
        candidates: List[EnrichedCandidate],
        x_vars: Dict[int, cp_model.IntVar],
        weights: Any,  # OptimizationWeights
    ) -> None:
        """
        Phase 4 (Priority 4): Minimise total operational risk and delay penalties (USD-normalised).
        Economic cost and demand fulfilment are already fixed by Phases 2 & 3.
        """
        risk_expr = []
        for idx, cand in enumerate(candidates):
            _, ta_hrs, risk_pts, cong_proxy = self.calculate_candidate_cost_components(cand)

            delay_penalty_usd = int(round(ta_hrs * weights.delay_cost_per_hour_usd))
            risk_penalty_usd = int(round(risk_pts * weights.risk_cost_per_point_usd))
            cong_penalty_usd = int(round((cong_proxy / 10.0) * weights.congestion_proxy_cost_per_index_usd))

            risk_expr.append(x_vars[idx] * (delay_penalty_usd + risk_penalty_usd + cong_penalty_usd))

        model.Minimize(sum(risk_expr) if risk_expr else 0)

    # ------------------------------------------------------------------
    # WEIGHTED (scalar) mode — NOT lexicographic, retained for legacy use
    # ------------------------------------------------------------------

    def build_weighted_objective(
        self,
        model: cp_model.CpModel,
        candidates: List[EnrichedCandidate],
        x_vars: Dict[int, cp_model.IntVar],
        q_vars: Dict[int, cp_model.IntVar],
        shortage_vars: Dict[str, cp_model.IntVar],
        request: OptimizationRequest,
    ) -> None:
        """
        WEIGHTED SCALAR OBJECTIVE (single-pass USD-normalised).

        Constructs a single objective expression combining economic cost,
        delay penalties, risk penalties, congestion proxy penalties, and
        commodity shortage penalties into one weighted sum.

        This is NOT a lexicographic or hierarchical objective.
        Priority ordering is approximated by penalty weight magnitudes only,
        and the solver may trade demand fulfilment against cost depending on
        relative weight values.

        Use ``solve_hierarchical=True`` for genuine lexicographic optimisation.
        """
        weights = request.weights
        total_cost_expr = []

        for idx, cand in enumerate(candidates):
            deliv_cost, ta_hrs, risk_pts, cong_proxy = self.calculate_candidate_cost_components(cand)

            # 1. Economic Cost ($)
            total_cost_expr.append(x_vars[idx] * deliv_cost)

            # 2. Delay Penalty ($)
            delay_penalty_usd = int(round(ta_hrs * weights.delay_cost_per_hour_usd))
            total_cost_expr.append(x_vars[idx] * delay_penalty_usd)

            # 3. Risk Penalty ($)
            risk_penalty_usd = int(round(risk_pts * weights.risk_cost_per_point_usd))
            total_cost_expr.append(x_vars[idx] * risk_penalty_usd)

            # 4. Congestion Proxy Penalty ($)
            cong_penalty_usd = int(round((cong_proxy / 10.0) * weights.congestion_proxy_cost_per_index_usd))
            total_cost_expr.append(x_vars[idx] * cong_penalty_usd)

        # 5. Shortage Penalties ($)
        for comm_name, shortage_var in shortage_vars.items():
            shortage_penalty_usd = int(round(weights.shortage_penalty_per_ton_usd))
            total_cost_expr.append(shortage_var * shortage_penalty_usd)

        model.Minimize(sum(total_cost_expr) if total_cost_expr else 0)
