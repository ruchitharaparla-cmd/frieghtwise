"""
Data contracts and schemas for FreightWise Stage 6 Optimization Engine.

Defines input parameters, enriched candidate schemas, solver status enums,
objective weights, and comprehensive output result contracts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class OptimizationStatus(str, Enum):
    """Solver and optimization execution status codes."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    ERROR = "ERROR"


class PlanType(str, Enum):
    """Type indicator for generated optimization plans."""
    EXECUTABLE_OPTIMAL = "EXECUTABLE_OPTIMAL"
    EXECUTABLE_ALTERNATIVE = "EXECUTABLE_ALTERNATIVE"
    EXPLORATORY_SENSITIVITY = "EXPLORATORY_SENSITIVITY"


@dataclass
class DemandTarget:
    """Target demand specification for a commodity over the planning horizon."""
    commodity: str
    target_quantity_tons: int
    tolerance_pct: float = 0.10  # 10% lower bound tolerance

    def validate(self) -> bool:
        if not self.commodity or not self.commodity.strip():
            raise ValueError("DemandTarget.commodity is required")
        if self.target_quantity_tons <= 0:
            raise ValueError(f"DemandTarget.target_quantity_tons must be > 0, got {self.target_quantity_tons}")
        return True


@dataclass
class OptimizationWeights:
    """
    Configurable parameters for single-pass weighted objective formulation.
    All penalties are normalized into USD currency equivalents.
    """
    delay_cost_per_hour_usd: float = 1500.0
    risk_cost_per_point_usd: float = 500.0
    congestion_proxy_cost_per_index_usd: float = 1000.0
    shortage_penalty_per_ton_usd: float = 150.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "delay_cost_per_hour_usd": self.delay_cost_per_hour_usd,
            "risk_cost_per_point_usd": self.risk_cost_per_point_usd,
            "congestion_proxy_cost_per_index_usd": self.congestion_proxy_cost_per_index_usd,
            "shortage_penalty_per_ton_usd": self.shortage_penalty_per_ton_usd,
        }


@dataclass
class OptimizationRequest:
    """Input request specification for an optimization run."""
    horizon_periods: int = 3
    planning_start_date: str = "2024-10-01"
    demand_targets: List[DemandTarget] = field(default_factory=list)
    max_charters_per_period: int = 5
    # -----------------------------------------------------------------------
    # CONFIGURABLE CARGO QUANTITY / CHARTER-SLOT PLANNING PARAMETERS.
    # These are NOT verified physical vessel DWT or vessel capacity values.
    # They represent the per-shipment cargo quantity bounds for optimisation
    # and must be adjusted to reflect actual charter agreements or domain
    # expertise before use in executable procurement decisions.
    # -----------------------------------------------------------------------
    min_batch_tons: int = 30000  # Minimum cargo per charter slot (MT) — planning parameter only
    max_batch_tons: int = 80000  # Maximum cargo per charter slot (MT) — planning parameter only
    batch_step_tons: int = 1000  # Quantity granularity step (MT) — planning parameter only
    weights: OptimizationWeights = field(default_factory=OptimizationWeights)
    # solve_hierarchical=True  → genuine 4-priority lexicographic sequential solve
    # solve_hierarchical=False → single-pass weighted-scalar USD objective (legacy mode)
    solve_hierarchical: bool = True
    include_exploratory_scenario: bool = True

    def validate(self) -> bool:
        if self.horizon_periods <= 0:
            raise ValueError("horizon_periods must be >= 1")
        if self.max_charters_per_period <= 0:
            raise ValueError("max_charters_per_period must be >= 1")
        for dt in self.demand_targets:
            dt.validate()
        return True


@dataclass
class CandidateRoute:
    """Base candidate route prior to stage enrichment."""
    origin: str
    destination_port: str
    commodity: str
    period: int
    forecast_date: str

    @property
    def candidate_id(self) -> str:
        return f"{self.origin}_to_{self.destination_port}_{self.commodity.replace(' ', '_')}_P{self.period}"


@dataclass
class EnrichedCandidate:
    """Candidate route enriched with Stage 2, 3, 4, and 5 metadata."""
    candidate: CandidateRoute
    stage4_status: str  # FEASIBLE | INFEASIBLE | DATA_UNAVAILABLE
    stage4_violated_constraints: List[str] = field(default_factory=list)
    stage4_unavailable_constraints: List[str] = field(default_factory=list)
    forecast_freight_usd_day: float = 0.0
    turnaround_hours: float = 0.0
    delay_risk_score: float = 0.0
    congestion_proxy_score: float = 0.0
    congestion_data_scope: str = "GLOBAL_CONGESTION_PROXY"
    voyage_cost_usd: float = 0.0
    commercial_risk_score: float = 0.0
    vessel_archetype: str = "Bulk Carrier Handysize Archetype Slot"

    @property
    def is_feasible(self) -> bool:
        return self.stage4_status == "FEASIBLE"

    @property
    def is_data_unavailable(self) -> bool:
        return self.stage4_status == "DATA_UNAVAILABLE"


@dataclass
class VoyageAllocation:
    """Individual procurement and charter voyage decision in an optimization plan."""
    allocation_id: str
    period: int
    forecast_date: str
    origin: str
    destination_port: str
    commodity: str
    cargo_quantity_tons: int
    vessel_archetype: str  # Strictly archetype slot, no fabricated IMO/vessel IDs
    forecast_freight_usd_day: float
    voyage_cost_usd: float
    turnaround_hours: float
    delay_risk_score: float
    congestion_proxy_score: float
    congestion_data_scope: str  # Strictly "GLOBAL_CONGESTION_PROXY"
    stage4_status: str  # "FEASIBLE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocation_id": self.allocation_id,
            "period": self.period,
            "forecast_date": self.forecast_date,
            "origin": self.origin,
            "destination_port": self.destination_port,
            "commodity": self.commodity,
            "cargo_quantity_tons": self.cargo_quantity_tons,
            "vessel_archetype": self.vessel_archetype,
            "forecast_freight_usd_day": self.forecast_freight_usd_day,
            "voyage_cost_usd": self.voyage_cost_usd,
            "turnaround_hours": self.turnaround_hours,
            "delay_risk_score": self.delay_risk_score,
            "congestion_proxy_score": self.congestion_proxy_score,
            "congestion_data_scope": self.congestion_data_scope,
            "stage4_status": self.stage4_status,
        }


@dataclass
class OptimizationPlan:
    """Complete optimization plan containing a set of voyage allocations."""
    plan_id: str
    plan_type: str  # EXECUTABLE_OPTIMAL | EXECUTABLE_ALTERNATIVE | EXPLORATORY_SENSITIVITY
    is_primary_optimal: bool
    objective_value: float
    total_cost_usd: float
    total_cargo_tons: int
    expected_delay_hours: float
    average_risk_score: float
    allocations: List[VoyageAllocation] = field(default_factory=list)
    # Solver mode under which this plan was produced.
    # "LEXICOGRAPHIC" → genuine 4-priority hierarchical sequential solve.
    # "WEIGHTED"       → single-pass USD-normalised weighted scalar objective.
    objective_mode: str = "WEIGHTED"
    # Per-priority achieved values from the lexicographic solve phases.
    # Populated only when objective_mode == "LEXICOGRAPHIC".
    # Keys: p2_shortage_tons, p3_economic_cost_usd, p4_risk_penalty_usd.
    lexicographic_achieved_values: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_type": self.plan_type,
            "is_primary_optimal": self.is_primary_optimal,
            "objective_mode": self.objective_mode,
            "objective_value": self.objective_value,
            "total_cost_usd": self.total_cost_usd,
            "total_cargo_tons": self.total_cargo_tons,
            "expected_delay_hours": self.expected_delay_hours,
            "average_risk_score": self.average_risk_score,
            "lexicographic_achieved_values": self.lexicographic_achieved_values,
            "allocations": [alloc.to_dict() for alloc in self.allocations],
        }


@dataclass
class UnavailableCandidateReport:
    """Report item for a Stage 4 DATA_UNAVAILABLE candidate excluded from default executable plans."""
    candidate_id: str
    origin: str
    destination_port: str
    commodity: str
    period: int
    stage4_status: str  # "DATA_UNAVAILABLE"
    missing_verification_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "origin": self.origin,
            "destination_port": self.destination_port,
            "commodity": self.commodity,
            "period": self.period,
            "stage4_status": self.stage4_status,
            "missing_verification_reasons": self.missing_verification_reasons,
        }


@dataclass
class CandidateStatusSummary:
    """Summary counts of candidate route evaluations."""
    total_generated: int = 0
    feasible_count: int = 0
    infeasible_count: int = 0
    data_unavailable_count: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "total_generated": self.total_generated,
            "feasible_count": self.feasible_count,
            "infeasible_count": self.infeasible_count,
            "data_unavailable_count": self.data_unavailable_count,
        }


@dataclass
class OptimizationResult:
    """Master output contract for Stage 6 Optimization Engine."""
    run_id: str
    solver_status: str  # OPTIMAL | FEASIBLE | INFEASIBLE | DATA_UNAVAILABLE | ERROR
    execution_time_seconds: float
    primary_executable_plan: Optional[OptimizationPlan]
    alternative_executable_plans: List[OptimizationPlan] = field(default_factory=list)
    unavailable_candidates: List[UnavailableCandidateReport] = field(default_factory=list)
    scenario_results: Dict[str, OptimizationPlan] = field(default_factory=dict)
    candidate_summary: CandidateStatusSummary = field(default_factory=CandidateStatusSummary)
    data_scope_notes: List[str] = field(default_factory=list)
    service_version: str = "stage6_v1.0.0"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "solver_status": self.solver_status,
            "execution_time_seconds": self.execution_time_seconds,
            "primary_executable_plan": self.primary_executable_plan.to_dict() if self.primary_executable_plan else None,
            "alternative_executable_plans": [plan.to_dict() for plan in self.alternative_executable_plans],
            "unavailable_candidates": [cand.to_dict() for cand in self.unavailable_candidates],
            "scenario_results": {name: plan.to_dict() for name, plan in self.scenario_results.items()},
            "candidate_summary": self.candidate_summary.to_dict(),
            "data_scope_notes": self.data_scope_notes,
            "service_version": self.service_version,
            "timestamp": self.timestamp,
        }
