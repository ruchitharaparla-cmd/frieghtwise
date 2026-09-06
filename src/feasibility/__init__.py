"""
FreightWise Stage 4 — Vessel & Port Feasibility / Rule-Based Constraint Engine.

Deterministic, rule-based feasibility evaluation for vessel-port-route-cargo combinations.
No ML models; no synthetic data generation; explicit DATA_UNAVAILABLE handling for missing constraints.

Core Components:
- VesselPortFeasibilityService: Production API
- FeasibilityEvaluator: Rule orchestration
- Constraint rules: Vessel, port, cargo, route compatibility
- Data loader: Verified constraint data from Stage 1 sources
- Contracts: Input/output schemas with validation
"""

from .service import VesselPortFeasibilityService
from .evaluator import FeasibilityEvaluator
from .exceptions import (
    DataUnavailableError,
    InvalidConstraintError,
    IndianPortSpecsUnavailableError,
    PortSpecsUnavailableError,
)

__all__ = [
    "VesselPortFeasibilityService",
    "FeasibilityEvaluator",
    "DataUnavailableError",
    "InvalidConstraintError",
    "IndianPortSpecsUnavailableError",
    "PortSpecsUnavailableError",
]
