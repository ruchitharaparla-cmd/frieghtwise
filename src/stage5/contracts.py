"""Public Stage 5 output contracts and configurable project parameters."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


COST_STATUSES = frozenset({"KNOWN", "ESTIMATED", "UNAVAILABLE"})
RISK_STATUSES = frozenset({"KNOWN", "ESTIMATED", "UNAVAILABLE", "HISTORICAL_CONTEXT_ONLY"})


@dataclass(frozen=True)
class ProjectParameters:
    """Configurable project parameters, not universal maritime constants."""

    default_currency: str = "USD"
    hours_per_day: float = 24.0
    required_cost_components: tuple[str, ...] = (
        "freight",
        "bunker",
        "port_charges",
        "demurrage",
    )
    source_label: str = "project_parameters"

    def to_dict(self) -> Dict[str, Any]:
        values = asdict(self)
        values["required_cost_components"] = list(self.required_cost_components)
        return values


@dataclass
class CostRiskEvaluation:
    cost_components: Dict[str, Dict[str, Any]]
    total_known_cost: Optional[float]
    cost_completeness: str
    missing_cost_components: List[str]
    risk_components: Dict[str, Dict[str, Any]]
    risk_status: str
    risk_completeness: str
    feasibility: Dict[str, Any]
    calculation_assumptions: List[str]
    project_parameters: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)