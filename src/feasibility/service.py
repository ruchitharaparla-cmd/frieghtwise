"""
Production Service for FreightWise Stage 4 — Vessel & Port Feasibility.

Public API for feasibility checks, batch evaluation, and human-readable explanations.
Wraps FeasibilityEvaluator for downstream Stage 5/6 consumption.
"""

import hashlib
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.feasibility.contracts import (
    VesselSpec,
    PortSpec,
    RouteSpec,
    CargoSpec,
    FeasibilityResult,
)
from src.feasibility.data_loader import ConstraintDataLoader
from src.feasibility.evaluator import FeasibilityEvaluator


def compute_code_hash(filepath: str) -> str:
    """Compute SHA-256 hash of service code file."""
    if not os.path.exists(filepath):
        return "UNKNOWN_HASH"
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class VesselPortFeasibilityService:
    """
    Production service for vessel-port-route-cargo feasibility evaluation.

    Public API:
    - check_feasibility(): Single vessel-port-route-cargo check
    - check_batch(): Evaluate multiple vessels to same port/route/cargo
    - explain(): Generate human-readable explanation

    All evaluation is deterministic and rule-based; no ML or synthetic data.
    Missing constraint data produces explicit DATA_UNAVAILABLE status.
    """

    def __init__(
        self,
        evaluator: Optional[FeasibilityEvaluator] = None,
        data_loader: Optional[ConstraintDataLoader] = None,
        auto_load: bool = True,
    ):
        self.data_loader = data_loader or ConstraintDataLoader()
        self.evaluator = evaluator or FeasibilityEvaluator(self.data_loader)
        self.service_version = "stage4_v1.0.0"
        self.code_hash = compute_code_hash(__file__)[:16]

        if auto_load:
            self.data_loader.load_all()

    def check_feasibility(
        self,
        vessel: Dict[str, Any],
        destination_port: str,
        destination_country: str,
        origin_country: str,
        cargo_type: str,
        cargo_weight_tons: Optional[float] = None,
        eval_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Single feasibility check for vessel-port-route-cargo combination.

        Args:
            vessel: Dict with keys: ship_type, maintenance_status, draft_meters (optional),
                   cargo_weight_tons (optional), route_type (optional), vessel_id (optional)
            destination_port: Port name (e.g., "Paradip SEA")
            destination_country: Country (e.g., "India")
            origin_country: Origin country (e.g., "Australia")
            cargo_type: Commodity type (e.g., "Iron Ore")
            cargo_weight_tons: Optional cargo weight for capacity check
            eval_date: Optional ISO date string for congestion lookup (not used in Stage 4)

        Returns:
            Dict with feasibility result (FEASIBLE, INFEASIBLE, DATA_UNAVAILABLE),
            violated/unavailable constraints, explanation, and metadata.

        Raises:
            ValueError: If required input fields missing or invalid
        """
        # Build input objects from dicts
        vessel_spec = VesselSpec(
            ship_type=vessel.get("ship_type"),
            maintenance_status=vessel.get("maintenance_status"),
            draft_meters=vessel.get("draft_meters"),
            cargo_weight_tons=cargo_weight_tons or vessel.get("cargo_weight_tons"),
            route_type=vessel.get("route_type"),
            engine_type=vessel.get("engine_type"),
            loa_meters=vessel.get("loa_meters"),
            beam_meters=vessel.get("beam_meters"),
            max_dwt_tons=vessel.get("max_dwt_tons"),
            vessel_id=vessel.get("vessel_id"),
        )

        port_spec = PortSpec(
            port_name=destination_port,
            country=destination_country,
            port_type=None,  # Not used in Stage 4
            max_channel_depth_meters=None,  # Not available for Indian ports
            berth_loa_meters=None,
            berth_beam_meters=None,
            berth_count=None,
        )

        route_spec = RouteSpec(
            origin_country=origin_country,
            destination_country=destination_country,
            destination_port=destination_port,
        )

        cargo_spec = CargoSpec(
            commodity_type=cargo_type,
            weight_tons=cargo_weight_tons,
        )

        # Evaluate
        result = self.evaluator.evaluate(vessel_spec, port_spec, route_spec, cargo_spec)

        # Convert to dict
        return result.to_dict()

    def check_batch(
        self,
        vessel_list: List[Dict[str, Any]],
        destination_port: str,
        destination_country: str,
        origin_country: str,
        cargo_type: str,
        cargo_weight_tons: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Batch feasibility checks for multiple vessels to same port/route/cargo.

        Args:
            vessel_list: List of vessel dicts (each must have ship_type, maintenance_status)
            destination_port, destination_country, origin_country, cargo_type: Shared route/cargo
            cargo_weight_tons: Optional shared cargo weight

        Returns:
            List of feasibility results, one per vessel
        """
        results = []
        for vessel in vessel_list:
            result = self.check_feasibility(
                vessel=vessel,
                destination_port=destination_port,
                destination_country=destination_country,
                origin_country=origin_country,
                cargo_type=cargo_type,
                cargo_weight_tons=cargo_weight_tons,
            )
            results.append(result)
        return results

    def explain(self, feasibility_result: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of feasibility result.

        Args:
            feasibility_result: Result dict from check_feasibility()

        Returns:
            Formatted string suitable for UI display
        """
        lines = [
            f"Feasibility Check: {feasibility_result['origin']} → {feasibility_result['destination']} (India)",
            f"Cargo: {feasibility_result['cargo_type']}",
            f"Status: {feasibility_result['feasibility_status']}",
            "",
        ]

        if feasibility_result['evaluated_constraints']:
            lines.append("Evaluated Constraints (PASSED):")
            for constraint in feasibility_result['evaluated_constraints']:
                lines.append(f"  ✓ {constraint}")
            lines.append("")

        if feasibility_result['violated_constraints']:
            lines.append("Violated Constraints (FAILED):")
            for constraint in feasibility_result['violated_constraints']:
                lines.append(f"  ✗ {constraint}")
            lines.append("")

        if feasibility_result['unavailable_constraints']:
            lines.append("Unavailable Constraints (CANNOT VERIFY):")
            for constraint in feasibility_result['unavailable_constraints']:
                lines.append(f"  ⚠ {constraint}")
            lines.append("")

        lines.append(feasibility_result['explanation'])

        return "\n".join(lines)
