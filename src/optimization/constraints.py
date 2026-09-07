"""
Constraint builder for Google OR-Tools CP-SAT model in Stage 6 Optimization Engine.

Defines decision variables (route selection, cargo quantity) and hard mathematical
constraints (quantity bounds, demand fulfillment, period charter limits).
"""

from typing import List, Dict, Any, Tuple
from ortools.sat.python import cp_model

from src.optimization.contracts import EnrichedCandidate, OptimizationRequest, DemandTarget


class OptimizationConstraintBuilder:
    """Constructs CP-SAT decision variables and hard mathematical constraints."""

    def build_variables_and_constraints(
        self,
        model: cp_model.CpModel,
        candidates: List[EnrichedCandidate],
        request: OptimizationRequest,
    ) -> Tuple[Dict[int, cp_model.IntVar], Dict[int, cp_model.IntVar], Dict[str, cp_model.IntVar]]:
        """
        Creates decision variables and adds hard constraints to CpModel.

        Returns:
            - x_vars: Dict[cand_idx -> binary IntVar x_i]
            - q_vars: Dict[cand_idx -> integer IntVar q_i (metric tons)]
            - shortage_vars: Dict[commodity_name -> integer IntVar shortage_c (metric tons)]
        """
        x_vars: Dict[int, cp_model.IntVar] = {}
        q_vars: Dict[int, cp_model.IntVar] = {}
        shortage_vars: Dict[str, cp_model.IntVar] = {}

        # 1. Create Decision Variables for Candidates
        for idx, cand in enumerate(candidates):
            cand_id = cand.candidate.candidate_id
            x_vars[idx] = model.NewBoolVar(f"x_{idx}_{cand_id}")
            q_vars[idx] = model.NewIntVar(0, request.max_batch_tons, f"q_{idx}_{cand_id}")

            # 2. Hard Linking Constraints between x_i and q_i
            # If x_i == 0, then q_i == 0
            # If x_i == 1, then min_batch <= q_i <= max_batch
            model.Add(q_vars[idx] >= request.min_batch_tons * x_vars[idx])
            model.Add(q_vars[idx] <= request.max_batch_tons * x_vars[idx])

        # 3. Period Charter Limits
        for period in range(1, request.horizon_periods + 1):
            period_x_vars = [
                x_vars[idx]
                for idx, cand in enumerate(candidates)
                if cand.candidate.period == period
            ]
            if period_x_vars:
                model.Add(sum(period_x_vars) <= request.max_charters_per_period)

        # 4. Commodity Demand Fulfillment Constraints
        for dt in request.demand_targets:
            comm_name = dt.commodity
            target_tons = dt.target_quantity_tons
            min_target_tons = int(target_tons * (1.0 - dt.tolerance_pct))

            comm_cand_indices = [
                idx
                for idx, cand in enumerate(candidates)
                if cand.candidate.commodity.lower() == comm_name.lower()
                or (
                    "coal" in comm_name.lower()
                    and cand.candidate.commodity.lower() in ["coal", "coke and briquettes"]
                )
            ]

            shortage_var = model.NewIntVar(0, target_tons, f"shortage_{comm_name}")
            shortage_vars[comm_name] = shortage_var

            if comm_cand_indices:
                total_procured_q = sum(q_vars[idx] for idx in comm_cand_indices)
                # Demand equation: Total Procured + Shortage >= Target
                model.Add(total_procured_q + shortage_var >= target_tons)
            else:
                # If no candidates match commodity, shortage equals full target
                model.Add(shortage_var == target_tons)

        return x_vars, q_vars, shortage_vars
