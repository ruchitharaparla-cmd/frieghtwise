"""
Main Optimization Engine Orchestrator for FreightWise Stage 6.

Coordinates candidate route building, Stage 4 feasibility filtering, CP-SAT solving,
solution extraction, and result reporting.
"""

from typing import List, Dict, Any, Optional
import time
import uuid

from src.optimization.contracts import (
    OptimizationRequest,
    OptimizationResult,
    CandidateStatusSummary,
    OptimizationStatus,
    PlanType,
)
from src.optimization.candidate_builder import CandidateBuilder, CandidateBuildResult
from src.optimization.cp_sat_solver import CPSatOptimizationSolver


class OptimizationEngine:
    """Orchestrates candidate generation, feasibility filtering, solving, and reporting."""

    def __init__(
        self,
        candidate_builder: Optional[CandidateBuilder] = None,
        solver: Optional[CPSatOptimizationSolver] = None,
    ):
        self.candidate_builder = candidate_builder or CandidateBuilder()
        self.solver = solver or CPSatOptimizationSolver()

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """
        Executes end-to-end optimization pipeline for a request:
        1. Validate request parameters.
        2. Build Cartesian candidates & apply Stage 4 filtering.
        3. Solve CP-SAT model over FEASIBLE candidates.
        4. Package result with executable plans, unavailable candidate reports, and scope notes.
        """
        start_time = time.time()
        run_id = f"OPT_{uuid.uuid4().hex[:8].upper()}"

        request.validate()

        # 1. Build and filter candidate routes
        build_result: CandidateBuildResult = self.candidate_builder.build_and_filter_candidates(request)

        # 2. Scope Notes
        data_scope_notes = [
            "Default Executable Plan includes only Stage 4 FEASIBLE candidates.",
            "Candidates with Stage 4 DATA_UNAVAILABLE are excluded from executable plans and reported separately.",
            "Indian Port Congestion metrics use GLOBAL_CONGESTION_PROXY scope explicitly.",
            "Vessel assignments represent Charter Archetypes / Slots (No physical ship IDs fabricated).",
        ]

        # Handle case where zero executable candidates exist
        if not build_result.executable_candidates:
            return OptimizationResult(
                run_id=run_id,
                solver_status=OptimizationStatus.INFEASIBLE.value,
                execution_time_seconds=time.time() - start_time,
                primary_executable_plan=None,
                alternative_executable_plans=[],
                unavailable_candidates=build_result.unavailable_candidates,
                candidate_summary=build_result.summary,
                data_scope_notes=data_scope_notes + ["Zero Stage 4 FEASIBLE candidates available."],
            )

        # 3. Execute CP-SAT Optimization Solver
        solver_status, primary_plan, alternative_plans, solver_time = self.solver.solve(
            candidates=build_result.executable_candidates,
            request=request,
            max_time_seconds=10.0,
            extract_alternatives=True,
        )

        total_exec_time = time.time() - start_time

        return OptimizationResult(
            run_id=run_id,
            solver_status=solver_status,
            execution_time_seconds=total_exec_time,
            primary_executable_plan=primary_plan,
            alternative_executable_plans=alternative_plans,
            unavailable_candidates=build_result.unavailable_candidates,
            candidate_summary=build_result.summary,
            data_scope_notes=data_scope_notes,
        )
