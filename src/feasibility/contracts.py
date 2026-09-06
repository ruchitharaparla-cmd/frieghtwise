"""
Data contracts and schemas for FreightWise Stage 4 Feasibility Engine.

Defines input/output contracts, constraint data structures, and validation rules.
All contracts include explicit handling for missing/unavailable fields.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


# ============================================================================
# Supported Commodities & Vessel Types
# ============================================================================

SUPPORTED_COMMODITIES = [
    "Iron Ore",
    "Coal",
    "Coke and Briquettes",
    "Fertilizers Manufactured",
    "Fertilizers Crude",
    "Petroleum Products",
    "Petroleum Crude",
]

SUPPORTED_VESSEL_TYPES = [
    "Bulk Carrier",
    "Tanker",
    "Fish Carrier",
    "Container Ship",
]

# Commodity-to-vessel type compatibility matrix
COMMODITY_TO_VESSEL_TYPES = {
    "Iron Ore": ["Bulk Carrier"],
    "Coal": ["Bulk Carrier"],
    "Coke and Briquettes": ["Bulk Carrier"],
    "Fertilizers Manufactured": ["Bulk Carrier"],
    "Fertilizers Crude": ["Bulk Carrier"],
    "Petroleum Products": ["Tanker"],
    "Petroleum Crude": ["Tanker"],
}

# Indian sea ports with no verified infrastructure specs
INDIAN_SEA_PORTS = [
    "Paradip SEA",
    "Dhamra(Chandbali)",
    "Dhamra (Chandbali)",
    "Visakhapatnam SEA",
    "Visakhapatnam",
    "Krishnapatnam",
    "Gangavaram PORT",
    "Gangavaram",
    "Kolkata SEA",
    "Kolkata",
    "Gopalpur PORT",
    "Gopalpur",
]

# ============================================================================
# Input Data Contracts
# ============================================================================


@dataclass
class VesselSpec:
    """
    Input specification for a vessel.

    Required fields: ship_type, maintenance_status
    Verified optional fields: draft_meters, cargo_weight_tons, route_type

    All missing required fields must be caught at validation time.
    """
    ship_type: str
    maintenance_status: str
    draft_meters: Optional[float] = None
    cargo_weight_tons: Optional[float] = None
    route_type: Optional[str] = None
    engine_type: Optional[str] = None
    loa_meters: Optional[float] = None  # Length Overall — NOT in current dataset
    beam_meters: Optional[float] = None  # Beam — NOT in current dataset
    max_dwt_tons: Optional[float] = None  # Deadweight tonnage — NOT in current dataset
    vessel_id: Optional[str] = None

    def validate(self) -> bool:
        """Validates required vessel fields."""
        if not self.ship_type or self.ship_type.strip() == "":
            raise ValueError("vessel.ship_type is required")
        if not self.maintenance_status or self.maintenance_status.strip() == "":
            raise ValueError("vessel.maintenance_status is required")
        if self.ship_type not in SUPPORTED_VESSEL_TYPES:
            raise ValueError(f"vessel.ship_type '{self.ship_type}' not in supported types")
        return True


@dataclass
class PortSpec:
    """
    Input specification for a destination port.

    Required fields: port_name, country

    Infrastructure fields (max_channel_depth_meters, berth_loa_meters, berth_beam_meters)
    are NEVER available for Indian ports; other global ports may have partial specs.
    """
    port_name: str
    country: str
    port_type: Optional[str] = None
    max_channel_depth_meters: Optional[float] = None
    berth_loa_meters: Optional[float] = None
    berth_beam_meters: Optional[float] = None
    berth_count: Optional[int] = None

    def validate(self) -> bool:
        """Validates required port fields."""
        if not self.port_name or self.port_name.strip() == "":
            raise ValueError("port.port_name is required")
        if not self.country or self.country.strip() == "":
            raise ValueError("port.country is required")
        return True

    def is_indian_port(self) -> bool:
        """Checks if this is an identified Indian port (no verified specs available)."""
        return self.country.lower() == "india" or any(
            indicator in self.port_name for indicator in INDIAN_SEA_PORTS
        )


@dataclass
class RouteSpec:
    """
    Input specification for a trade route.
    """
    origin_country: str
    destination_country: str
    destination_port: str

    def validate(self) -> bool:
        """Validates route fields."""
        if not self.origin_country or self.origin_country.strip() == "":
            raise ValueError("route.origin_country is required")
        if not self.destination_country or self.destination_country.strip() == "":
            raise ValueError("route.destination_country is required")
        if not self.destination_port or self.destination_port.strip() == "":
            raise ValueError("route.destination_port is required")
        return True


@dataclass
class CargoSpec:
    """
    Input specification for cargo.
    """
    commodity_type: str
    weight_tons: Optional[float] = None
    hazmat_class: Optional[str] = None

    def validate(self) -> bool:
        """Validates cargo fields."""
        if not self.commodity_type or self.commodity_type.strip() == "":
            raise ValueError("cargo.commodity_type is required")
        return True


# ============================================================================
# Rule Evaluation Results
# ============================================================================


@dataclass
class RuleResult:
    """Result of evaluating a single constraint rule."""
    rule_id: str
    description: str
    status: str  # PASS | FAIL | DATA_UNAVAILABLE
    reason: str
    severity: str = "INFO"  # INFO | WARNING | ERROR
    required_fields: List[str] = field(default_factory=list)
    available_fields: List[str] = field(default_factory=list)

    def is_pass(self) -> bool:
        return self.status == "PASS"

    def is_fail(self) -> bool:
        return self.status == "FAIL"

    def is_unavailable(self) -> bool:
        return self.status == "DATA_UNAVAILABLE"


# ============================================================================
# Feasibility Result Output Contract
# ============================================================================


@dataclass
class FeasibilityResult:
    """
    Output contract for feasibility evaluation.

    Status Semantics:
    - FEASIBLE: All required constraints verified and pass
    - INFEASIBLE: All required constraints verified but at least one fails
    - DATA_UNAVAILABLE: One or more required constraints missing; cannot reach conclusion
    """
    feasibility_status: str  # FEASIBLE | INFEASIBLE | DATA_UNAVAILABLE
    vessel_id: Optional[str]
    origin: str
    destination: str
    destination_country: str
    cargo_type: str
    violated_constraints: List[str] = field(default_factory=list)
    unavailable_constraints: List[str] = field(default_factory=list)
    evaluated_constraints: List[str] = field(default_factory=list)
    explanation: str = ""
    detailed_results: List[Dict[str, Any]] = field(default_factory=list)
    data_scope_version: str = "Stage1_2024-Q3"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z")
    service_version: str = "stage4_v1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "feasibility_status": self.feasibility_status,
            "vessel_id": self.vessel_id,
            "origin": self.origin,
            "destination": self.destination,
            "destination_country": self.destination_country,
            "cargo_type": self.cargo_type,
            "violated_constraints": self.violated_constraints,
            "unavailable_constraints": self.unavailable_constraints,
            "evaluated_constraints": self.evaluated_constraints,
            "explanation": self.explanation,
            "detailed_results": self.detailed_results,
            "data_scope_version": self.data_scope_version,
            "timestamp": self.timestamp,
            "service_version": self.service_version,
        }
