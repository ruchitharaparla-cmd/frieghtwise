"""
Public Optimization Service facade for FreightWise Stage 6 Optimization Engine.

Provides clean entry point for external invocations, Stage 7 AI explanation layer,
and Stage 8 UI dashboard services.
"""

from typing import List, Dict, Any, Optional

from src.optimization.contracts import (
    OptimizationRequest,
    OptimizationResult,
    DemandTarget,
    OptimizationWeights,
)
from src.optimization.optimizer import OptimizationEngine
from src.optimization.scenario import ScenarioEvaluator


class OptimizationService:
    """Public facade service for Integrated Freight, Charter & Cargo Procurement Optimization."""

    def __init__(
        self,
        engine: Optional[OptimizationEngine] = None,
        scenario_evaluator: Optional[ScenarioEvaluator] = None,
    ):
        self.engine = engine or OptimizationEngine()
        self.scenario_evaluator = scenario_evaluator or ScenarioEvaluator()

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """
        Executes complete optimization run including primary plan, alternatives,
        unavailable candidate reporting, and multi-scenario evaluation.
        """
        # 1. Run main optimization pipeline
        result = self.engine.optimize(request)

        # 2. Run scenario evaluation if primary plan succeeded or exploratory scenario requested
        if result.primary_executable_plan or request.include_exploratory_scenario:
            build_result = self.engine.candidate_builder.build_and_filter_candidates(request)
            scenario_matrix = self.scenario_evaluator.evaluate_scenarios(request, build_result)
            result.scenario_results = scenario_matrix

        return result

    def optimize_dict(
        self,
        horizon_periods: int = 3,
        planning_start_date: str = "2024-10-01",
        demand_targets: Optional[List[Dict[str, Any]]] = None,
        max_charters_per_period: int = 5,
    ) -> Dict[str, Any]:
        """
        Dictionary-friendly convenience wrapper for API and UI consumption.
        """
        targets: List[DemandTarget] = []
        if demand_targets:
            for dt in demand_targets:
                targets.append(
                    DemandTarget(
                        commodity=dt.get("commodity", "Coal"),
                        target_quantity_tons=int(dt.get("target_quantity_tons", 60000)),
                        tolerance_pct=float(dt.get("tolerance_pct", 0.10)),
                    )
                )
        else:
            # Default SIH demonstration target: 60,000 MT Coal
            targets.append(DemandTarget(commodity="Coal", target_quantity_tons=60000))

        request = OptimizationRequest(
            horizon_periods=horizon_periods,
            planning_start_date=planning_start_date,
            demand_targets=targets,
            max_charters_per_period=max_charters_per_period,
        )

        res = self.optimize(request)
        return res.to_dict()
