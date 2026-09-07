"""
FreightWise Stage 6 — Integrated Freight, Charter & Cargo Procurement Optimization Engine.

Provides optimization models, input adapters, candidate filters, CP-SAT solvers,
scenario evaluation engines, and solution pool generators.
"""

from src.optimization.contracts import (
    OptimizationResult,
    OptimizationPlan,
    VoyageAllocation,
    UnavailableCandidateReport,
    CandidateStatusSummary,
    OptimizationStatus,
    PlanType,
)
from src.optimization.service import OptimizationService

__all__ = [
    "OptimizationResult",
    "OptimizationPlan",
    "VoyageAllocation",
    "UnavailableCandidateReport",
    "CandidateStatusSummary",
    "OptimizationStatus",
    "PlanType",
    "OptimizationService",
]
