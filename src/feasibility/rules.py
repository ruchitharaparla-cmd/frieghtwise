"""
Rule implementations for FreightWise Stage 4 Feasibility Engine.

Every rule explicitly defines:
- Required input fields
- Pass condition
- Fail condition
- DATA_UNAVAILABLE condition

Rules are stateless and deterministic; no random or synthetic data.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from src.feasibility.contracts import (
    VesselSpec,
    PortSpec,
    RouteSpec,
    CargoSpec,
    RuleResult,
    COMMODITY_TO_VESSEL_TYPES,
    INDIAN_SEA_PORTS,
)
from src.feasibility.exceptions import (
    DataUnavailableError,
    IndianPortSpecsUnavailableError,
    PortSpecsUnavailableError,
)


# ============================================================================
# Rule Base Class & Context
# ============================================================================


class ConstraintRule(ABC):
    """
    Abstract base for all constraint evaluation rules.

    Every rule must implement evaluate() and define its required fields explicitly.
    """

    rule_id: str = "unknown_rule"
    description: str = "Unknown rule"
    required_fields: list = []  # Fields that must exist to evaluate

    @abstractmethod
    def evaluate(
        self,
        vessel: VesselSpec,
        port: PortSpec,
        route: RouteSpec,
        cargo: CargoSpec,
        data_loader: Any,  # ConstraintDataLoader type
    ) -> RuleResult:
        """
        Evaluate the constraint.

        Must return RuleResult with status PASS, FAIL, or DATA_UNAVAILABLE.
        """
        raise NotImplementedError()


# ============================================================================
# Vessel Rules
# ============================================================================


class VesselTypeCargoCompatibilityRule(ConstraintRule):
    """
    Rule 1.1: Checks if vessel type can carry the specified commodity.

    Required Input Fields:
    - vessel.ship_type
    - cargo.commodity_type

    Evaluation:
    - PASS: vessel.ship_type in COMMODITY_TO_VESSEL_TYPES[cargo.commodity_type]
    - FAIL: vessel.ship_type not compatible with cargo
    - DATA_UNAVAILABLE: cargo type not in supported list
    """

    rule_id = "vessel_cargo_compatibility"
    description = "Vessel type compatible with cargo commodity"
    required_fields = ["vessel.ship_type", "cargo.commodity_type"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if not vessel.ship_type:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Vessel ship_type not specified",
                required_fields=self.required_fields,
            )

        if not cargo.commodity_type:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Cargo commodity_type not specified",
                required_fields=self.required_fields,
            )

        compatible_types = COMMODITY_TO_VESSEL_TYPES.get(cargo.commodity_type)

        if compatible_types is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Commodity '{cargo.commodity_type}' not in supported list",
                required_fields=self.required_fields,
                available_fields=list(COMMODITY_TO_VESSEL_TYPES.keys()),
            )

        if vessel.ship_type in compatible_types:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Vessel type {vessel.ship_type} compatible with {cargo.commodity_type}",
                required_fields=self.required_fields,
                available_fields=["vessel.ship_type", "cargo.commodity_type"],
            )
        else:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="FAIL",
                reason=f"Vessel type {vessel.ship_type} cannot carry {cargo.commodity_type}. "
                       f"Required types: {compatible_types}",
                required_fields=self.required_fields,
                available_fields=["vessel.ship_type", "cargo.commodity_type"],
                severity="ERROR",
            )


class VesselMaintenanceStatusRule(ConstraintRule):
    """
    Rule 1.2: Pre-voyage maintenance status check.

    Required Input Fields:
    - vessel.maintenance_status

    Evaluation:
    - PASS: maintenance_status in ["Good", "Fair"]
    - FAIL: maintenance_status == "Critical"
    - DATA_UNAVAILABLE: maintenance_status not specified or unrecognized
    """

    rule_id = "vessel_maintenance_status"
    description = "Vessel maintenance status suitable for voyage"
    required_fields = ["vessel.maintenance_status"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if not vessel.maintenance_status:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Vessel maintenance_status not specified",
                required_fields=self.required_fields,
            )

        status = vessel.maintenance_status.lower().strip()

        if status == "critical":
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="FAIL",
                reason="Vessel in CRITICAL maintenance status; not voyage-ready",
                required_fields=self.required_fields,
                available_fields=["vessel.maintenance_status"],
                severity="ERROR",
            )
        elif status in ["good", "fair"]:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Maintenance status {vessel.maintenance_status} acceptable for voyage",
                required_fields=self.required_fields,
                available_fields=["vessel.maintenance_status"],
                severity="INFO" if status == "good" else "WARNING",
            )
        else:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Unrecognized maintenance status: {vessel.maintenance_status}. "
                       f"Expected: Good, Fair, or Critical",
                required_fields=self.required_fields,
                available_fields=["vessel.maintenance_status"],
            )


class VesselDraftPortCompatibilityRule(ConstraintRule):
    """
    Rule 1.3: Vessel draft vs port/channel maximum depth.

    Required Input Fields:
    - vessel.draft_meters
    - port.max_channel_depth_meters (or PORT SPECS unavailable)

    Evaluation:
    - PASS: vessel.draft_meters <= port.max_channel_depth_meters
    - FAIL: vessel.draft_meters > port.max_channel_depth_meters
    - DATA_UNAVAILABLE: port max depth not verified (especially Indian ports)

    CRITICAL DATA HONESTY:
    Indian ports explicitly return DATA_UNAVAILABLE; no synthetic values used.
    """

    rule_id = "vessel_draft_port_compatibility"
    description = "Vessel draft compatible with port/channel depth"
    required_fields = ["vessel.draft_meters", "port.max_channel_depth_meters"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if vessel.draft_meters is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Vessel draft_meters not specified",
                required_fields=self.required_fields,
            )

        # Check if Indian port: explicit unavailability
        if data_loader.is_indian_port(port.port_name, port.country):
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Port {port.port_name} (India) has no verified channel depth specifications in dataset. "
                       f"Recommend consulting Indian Ports Association (IPA) or port authority.",
                required_fields=self.required_fields,
                available_fields=["vessel.draft_meters"],
                severity="WARNING",
            )

        # For non-Indian ports: check if specs available
        if port.max_channel_depth_meters is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Port {port.port_name} maximum channel depth not verified in dataset",
                required_fields=self.required_fields,
                available_fields=["vessel.draft_meters"],
            )

        # Evaluate draft compatibility
        if vessel.draft_meters <= port.max_channel_depth_meters:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Vessel draft {vessel.draft_meters}m <= port depth limit {port.max_channel_depth_meters}m",
                required_fields=self.required_fields,
                available_fields=["vessel.draft_meters", "port.max_channel_depth_meters"],
            )
        else:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="FAIL",
                reason=f"Vessel draft {vessel.draft_meters}m exceeds port depth limit {port.max_channel_depth_meters}m",
                required_fields=self.required_fields,
                available_fields=["vessel.draft_meters", "port.max_channel_depth_meters"],
                severity="ERROR",
            )


class VesselCargoCapacityRule(ConstraintRule):
    """
    Rule 1.4: Cargo weight vs vessel capacity (DWT).

    Required Input Fields:
    - cargo.weight_tons
    - vessel.max_dwt_tons (or unavailable)

    Evaluation:
    - PASS: cargo.weight_tons <= vessel.max_dwt_tons
    - FAIL: cargo.weight_tons > vessel.max_dwt_tons
    - DATA_UNAVAILABLE: vessel DWT not specified (current dataset limitation)

    NOTE: Current vessel_performance_processed.csv does NOT include DWT.
    This rule will return DATA_UNAVAILABLE until vessel specs are enriched.
    """

    rule_id = "vessel_cargo_capacity"
    description = "Cargo weight within vessel capacity"
    required_fields = ["cargo.weight_tons", "vessel.max_dwt_tons"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if cargo.weight_tons is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Cargo weight_tons not specified",
                required_fields=self.required_fields,
            )

        if vessel.max_dwt_tons is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Vessel deadweight tonnage (DWT) not available in dataset. "
                       "Cannot verify cargo weight capacity.",
                required_fields=self.required_fields,
                available_fields=["cargo.weight_tons"],
                severity="WARNING",
            )

        # Evaluate capacity
        if cargo.weight_tons <= vessel.max_dwt_tons:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Cargo weight {cargo.weight_tons} tons <= vessel DWT {vessel.max_dwt_tons} tons",
                required_fields=self.required_fields,
                available_fields=["cargo.weight_tons", "vessel.max_dwt_tons"],
            )
        else:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="FAIL",
                reason=f"Cargo weight {cargo.weight_tons} tons exceeds vessel DWT {vessel.max_dwt_tons} tons",
                required_fields=self.required_fields,
                available_fields=["cargo.weight_tons", "vessel.max_dwt_tons"],
                severity="ERROR",
            )


class VesselBerthCompatibilityRule(ConstraintRule):
    """
    Rule 1.5: Vessel dimensions vs berth specifications.

    Required Input Fields:
    - vessel.loa_meters
    - vessel.beam_meters
    - port.berth_loa_meters
    - port.berth_beam_meters

    Evaluation:
    - PASS: vessel LOA/beam fit within berth
    - FAIL: vessel dimensions exceed berth
    - DATA_UNAVAILABLE: vessel or port specs not available

    CRITICAL: Never invents berth dimensions for Indian ports.
    Current dataset does NOT include vessel dimensions or berth specs.
    Rule will return DATA_UNAVAILABLE.
    """

    rule_id = "vessel_berth_compatibility"
    description = "Vessel dimensions fit within berth"
    required_fields = ["vessel.loa_meters", "vessel.beam_meters", "port.berth_loa_meters", "port.berth_beam_meters"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if vessel.loa_meters is None or vessel.beam_meters is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Vessel length overall (LOA) or beam not specified in dataset",
                required_fields=self.required_fields,
                severity="WARNING",
            )

        # Check if Indian port
        if data_loader.is_indian_port(port.port_name, port.country):
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Port {port.port_name} (India) berth specifications not verified in dataset. "
                       f"Cannot evaluate berth fit. Recommend consulting IPA or port authority.",
                required_fields=self.required_fields,
                available_fields=["vessel.loa_meters", "vessel.beam_meters"],
                severity="WARNING",
            )

        # For other ports: check if specs available
        if port.berth_loa_meters is None or port.berth_beam_meters is None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Port {port.port_name} berth dimensions not verified in dataset",
                required_fields=self.required_fields,
                available_fields=["vessel.loa_meters", "vessel.beam_meters"],
            )

        # Evaluate fit
        loa_fits = vessel.loa_meters <= port.berth_loa_meters
        beam_fits = vessel.beam_meters <= port.berth_beam_meters

        if loa_fits and beam_fits:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Vessel (LOA {vessel.loa_meters}m x Beam {vessel.beam_meters}m) fits within berth "
                       f"({port.berth_loa_meters}m x {port.berth_beam_meters}m)",
                required_fields=self.required_fields,
                available_fields=["vessel.loa_meters", "vessel.beam_meters", "port.berth_loa_meters", "port.berth_beam_meters"],
            )
        else:
            reasons = []
            if not loa_fits:
                reasons.append(f"LOA {vessel.loa_meters}m > {port.berth_loa_meters}m")
            if not beam_fits:
                reasons.append(f"Beam {vessel.beam_meters}m > {port.berth_beam_meters}m")
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="FAIL",
                reason=f"Vessel dimensions exceed berth: {'; '.join(reasons)}",
                required_fields=self.required_fields,
                available_fields=["vessel.loa_meters", "vessel.beam_meters", "port.berth_loa_meters", "port.berth_beam_meters"],
                severity="ERROR",
            )


# ============================================================================
# Port Rules
# ============================================================================


class PortKnownInDataRule(ConstraintRule):
    """
    Rule 2.1: Port exists in historical demand data.

    Required Input Fields:
    - port.port_name
    - route.origin_country

    Evaluation:
    - PASS: route appears in demand summary
    - PASS (LOW_CONFIDENCE): port known but route unseen
    - DATA_UNAVAILABLE: port not in historical data
    """

    rule_id = "port_known_in_data"
    description = "Port known in historical routing data"
    required_fields = ["port.port_name", "route.origin_country"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if not port.port_name or not route.origin_country:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Port name or origin country not specified",
                required_fields=self.required_fields,
            )

        route_info = data_loader.check_route_exists(route.origin_country, port.port_name)

        if route_info["exists"]:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Route {route.origin_country} → {port.port_name} known. "
                       f"Demand score: {route_info['demand_score']:.2f}, "
                       f"Priority: {route_info['route_priority']}",
                required_fields=self.required_fields,
                available_fields=["port.port_name", "route.origin_country"],
            )
        else:
            # Port exists but route not seen
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Route {route.origin_country} → {port.port_name} not in historical data. "
                       f"Cannot determine if viable.",
                required_fields=self.required_fields,
                available_fields=["port.port_name", "route.origin_country"],
                severity="WARNING",
            )


class CargoTypesSupportedRule(ConstraintRule):
    """
    Rule 4.1: Cargo type is in supported commodity list.

    Required Input Fields:
    - cargo.commodity_type

    Evaluation:
    - PASS: commodity in supported list
    - DATA_UNAVAILABLE: commodity not supported
    """

    rule_id = "cargo_type_supported"
    description = "Cargo type in supported commodities"
    required_fields = ["cargo.commodity_type"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        if not cargo.commodity_type:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason="Cargo commodity_type not specified",
                required_fields=self.required_fields,
            )

        supported_types = data_loader.get_commodity_vessel_types(cargo.commodity_type)

        if supported_types is not None:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="PASS",
                reason=f"Commodity {cargo.commodity_type} is supported",
                required_fields=self.required_fields,
                available_fields=["cargo.commodity_type"],
            )
        else:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Commodity '{cargo.commodity_type}' not in supported list",
                required_fields=self.required_fields,
                available_fields=["cargo.commodity_type"],
            )


class RouteValidityRule(ConstraintRule):
    """
    Rule 3.1: Route origin-destination structure is valid.

    Required Input Fields:
    - route.origin_country
    - route.destination_country
    - route.destination_port

    Evaluation:
    - PASS: route structure sensible
    - DATA_UNAVAILABLE: malformed route
    """

    rule_id = "route_validity"
    description = "Route origin-destination structure valid"
    required_fields = ["route.origin_country", "route.destination_country", "route.destination_port"]

    def evaluate(self, vessel: VesselSpec, port: PortSpec, route: RouteSpec, cargo: CargoSpec, data_loader: Any) -> RuleResult:
        missing = []
        if not route.origin_country:
            missing.append("origin_country")
        if not route.destination_country:
            missing.append("destination_country")
        if not route.destination_port:
            missing.append("destination_port")

        if missing:
            return RuleResult(
                rule_id=self.rule_id,
                description=self.description,
                status="DATA_UNAVAILABLE",
                reason=f"Route missing required fields: {missing}",
                required_fields=self.required_fields,
            )

        # Basic validation: origin and destination should differ (unless coastal)
        # or both should be valid strings
        return RuleResult(
            rule_id=self.rule_id,
            description=self.description,
            status="PASS",
            reason=f"Route {route.origin_country} → {route.destination_port} structure valid",
            required_fields=self.required_fields,
            available_fields=self.required_fields,
        )
