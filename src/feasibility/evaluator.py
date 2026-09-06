"""
Feasibility Evaluator for FreightWise Stage 4.

Orchestrates rule execution, result aggregation, and status determination.
All evaluation is deterministic; no randomization or synthetic data.
"""

from typing import List, Dict, Any

from src.feasibility.contracts import (
    VesselSpec,
    PortSpec,
    RouteSpec,
    CargoSpec,
    FeasibilityResult,
    RuleResult,
)
from src.feasibility.data_loader import ConstraintDataLoader
from src.feasibility.rules import (
    ConstraintRule,
    VesselTypeCargoCompatibilityRule,
    VesselMaintenanceStatusRule,
    VesselDraftPortCompatibilityRule,
    VesselCargoCapacityRule,
    VesselBerthCompatibilityRule,
    PortKnownInDataRule,
    CargoTypesSupportedRule,
    RouteValidityRule,
)
from src.feasibility.exceptions import DataUnavailableError


class FeasibilityEvaluator:
    """
    Orchestrates feasibility evaluation through rule execution and result aggregation.

    Execution Flow:
    1. Validate input contracts
    2. Execute rule set in defined order
    3. Aggregate results (pass/fail/unavailable counts)
    4. Determine overall feasibility status
    5. Generate explanation

    Status determination:
    - FEASIBLE: All rules evaluated; no failures; no critical unavailable constraints
    - INFEASIBLE: All constraints available; at least one rule fails
    - DATA_UNAVAILABLE: One or more critical constraints missing; cannot evaluate fully
    """

    def __init__(self, data_loader: ConstraintDataLoader):
        self.data_loader = data_loader

        # Define rule execution order (vessel → port → cargo → route)
        self.rules: List[ConstraintRule] = [
            VesselTypeCargoCompatibilityRule(),
            VesselMaintenanceStatusRule(),
            CargoTypesSupportedRule(),
            RouteValidityRule(),
            PortKnownInDataRule(),
            VesselDraftPortCompatibilityRule(),
            VesselCargoCapacityRule(),
            VesselBerthCompatibilityRule(),
        ]

    def evaluate(
        self,
        vessel: VesselSpec,
        port: PortSpec,
        route: RouteSpec,
        cargo: CargoSpec,
    ) -> FeasibilityResult:
        """
        Execute all rules and aggregate results.

        Returns:
            FeasibilityResult with status, violated/unavailable/evaluated constraints, explanation
        """
        # Validate inputs
        vessel.validate()
        port.validate()
        route.validate()
        cargo.validate()

        # Pre-load data
        self.data_loader.load_all()

        # Initialize result
        result = FeasibilityResult(
            feasibility_status="UNKNOWN",
            vessel_id=vessel.vessel_id,
            origin=route.origin_country,
            destination=port.port_name,
            destination_country=port.country,
            cargo_type=cargo.commodity_type,
        )

        # Execute all rules
        rule_results: List[RuleResult] = []
        for rule in self.rules:
            rule_result = rule.evaluate(vessel, port, route, cargo, self.data_loader)
            rule_results.append(rule_result)

        # Aggregate results
        self._aggregate_results(result, rule_results)

        # Determine overall status
        self._determine_status(result)

        # Generate explanation
        self._generate_explanation(result, rule_results)

        return result

    def _aggregate_results(self, result: FeasibilityResult, rule_results: List[RuleResult]) -> None:
        """Aggregate per-rule results into overall result."""
        for rule_result in rule_results:
            # Record detailed results
            result.detailed_results.append({
                "rule_id": rule_result.rule_id,
                "description": rule_result.description,
                "status": rule_result.status,
                "reason": rule_result.reason,
                "severity": rule_result.severity,
            })

            # Categorize rule outcome
            if rule_result.is_pass():
                result.evaluated_constraints.append(rule_result.rule_id)
            elif rule_result.is_fail():
                result.violated_constraints.append(rule_result.rule_id)
            elif rule_result.is_unavailable():
                result.unavailable_constraints.append(rule_result.rule_id)

    def _determine_status(self, result: FeasibilityResult) -> None:
        """
        Determine overall feasibility status based on rule outcomes.

        Logic:
        1. If any rules are DATA_UNAVAILABLE: status = DATA_UNAVAILABLE
        2. Else if any rules FAIL: status = INFEASIBLE
        3. Else (all rules PASS): status = FEASIBLE
        """
        if result.unavailable_constraints:
            result.feasibility_status = "DATA_UNAVAILABLE"
        elif result.violated_constraints:
            result.feasibility_status = "INFEASIBLE"
        else:
            result.feasibility_status = "FEASIBLE"

    def _generate_explanation(self, result: FeasibilityResult, rule_results: List[RuleResult]) -> None:
        """Generate human-readable explanation of feasibility result."""
        lines = []

        # Status summary
        lines.append(f"Feasibility Status: {result.feasibility_status}")

        # Passed constraints
        if result.evaluated_constraints:
            lines.append("\nEvaluated Constraints (PASSED):")
            for rule_id in result.evaluated_constraints:
                rule_result = next((r for r in rule_results if r.rule_id == rule_id), None)
                if rule_result:
                    lines.append(f"  ✓ {rule_result.description}")

        # Failed constraints
        if result.violated_constraints:
            lines.append("\nViolated Constraints (FAILED):")
            for rule_id in result.violated_constraints:
                rule_result = next((r for r in rule_results if r.rule_id == rule_id), None)
                if rule_result:
                    lines.append(f"  ✗ {rule_result.description}")
                    lines.append(f"      Reason: {rule_result.reason}")

        # Unavailable constraints
        if result.unavailable_constraints:
            lines.append("\nUnavailable Constraints (CANNOT VERIFY):")
            for rule_id in result.unavailable_constraints:
                rule_result = next((r for r in rule_results if r.rule_id == rule_id), None)
                if rule_result:
                    lines.append(f"  ⚠ {rule_result.description}")
                    lines.append(f"      Reason: {rule_result.reason}")

        # Recommendation
        lines.append("\nRecommendation:")
        if result.feasibility_status == "FEASIBLE":
            lines.append("  All constraints verified; voyage is feasible. Proceed to economic analysis.")
        elif result.feasibility_status == "INFEASIBLE":
            lines.append("  One or more constraints failed. Recommend alternative vessel or port.")
        elif result.feasibility_status == "DATA_UNAVAILABLE":
            lines.append("  Cannot verify all constraints. Recommend external data verification.")

        result.explanation = "\n".join(lines)
