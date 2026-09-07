"""
Contract validation tests for FreightWise Stage 4.

Tests data contract validation and error handling.
"""

import pytest
from src.feasibility.contracts import (
    VesselSpec,
    PortSpec,
    RouteSpec,
    CargoSpec,
    FeasibilityResult,
    RuleResult,
)


class TestVesselSpecContract:
    """Tests for vessel specification validation."""

    def test_valid_vessel_spec(self):
        """Valid vessel spec passes validation."""
        vessel = VesselSpec(
            ship_type="Bulk Carrier",
            maintenance_status="Good",
            draft_meters=10.0,
        )

        assert vessel.validate() is True

    def test_missing_ship_type_raises(self):
        """Missing ship_type raises ValueError."""
        vessel = VesselSpec(
            ship_type="",
            maintenance_status="Good",
        )

        with pytest.raises(ValueError, match="ship_type"):
            vessel.validate()

    def test_missing_maintenance_status_raises(self):
        """Missing maintenance_status raises ValueError."""
        vessel = VesselSpec(
            ship_type="Bulk Carrier",
            maintenance_status="",
        )

        with pytest.raises(ValueError, match="maintenance_status"):
            vessel.validate()

    def test_unsupported_ship_type_raises(self):
        """Unsupported ship_type raises ValueError."""
        vessel = VesselSpec(
            ship_type="Unicorn Ship",
            maintenance_status="Good",
        )

        with pytest.raises(ValueError, match="not in supported"):
            vessel.validate()

    def test_optional_fields_missing_ok(self):
        """Optional fields can be None."""
        vessel = VesselSpec(
            ship_type="Bulk Carrier",
            maintenance_status="Good",
            draft_meters=None,
            cargo_weight_tons=None,
        )

        assert vessel.validate() is True


class TestPortSpecContract:
    """Tests for port specification validation."""

    def test_valid_port_spec(self):
        """Valid port spec passes validation."""
        port = PortSpec(
            port_name="Test Port",
            country="Denmark",
        )

        assert port.validate() is True

    def test_missing_port_name_raises(self):
        """Missing port_name raises ValueError."""
        port = PortSpec(
            port_name="",
            country="Denmark",
        )

        with pytest.raises(ValueError, match="port_name"):
            port.validate()

    def test_missing_country_raises(self):
        """Missing country raises ValueError."""
        port = PortSpec(
            port_name="Test Port",
            country="",
        )

        with pytest.raises(ValueError, match="country"):
            port.validate()

    def test_is_indian_port_paradip(self):
        """Paradip is identified as Indian port."""
        port = PortSpec(
            port_name="Paradip SEA",
            country="India",
        )

        assert port.is_indian_port() is True

    def test_is_indian_port_by_country(self):
        """Port with India as country is Indian port."""
        port = PortSpec(
            port_name="Unknown Port",
            country="India",
        )

        assert port.is_indian_port() is True

    def test_is_not_indian_port_denmark(self):
        """Danish port is not Indian port."""
        port = PortSpec(
            port_name="Copenhagen",
            country="Denmark",
        )

        assert port.is_indian_port() is False


class TestRouteSpecContract:
    """Tests for route specification validation."""

    def test_valid_route_spec(self):
        """Valid route spec passes validation."""
        route = RouteSpec(
            origin_country="Australia",
            destination_country="India",
            destination_port="Paradip SEA",
        )

        assert route.validate() is True

    def test_missing_origin_raises(self):
        """Missing origin_country raises ValueError."""
        route = RouteSpec(
            origin_country="",
            destination_country="India",
            destination_port="Paradip SEA",
        )

        with pytest.raises(ValueError, match="origin_country"):
            route.validate()

    def test_missing_destination_country_raises(self):
        """Missing destination_country raises ValueError."""
        route = RouteSpec(
            origin_country="Australia",
            destination_country="",
            destination_port="Paradip SEA",
        )

        with pytest.raises(ValueError, match="destination_country"):
            route.validate()

    def test_missing_destination_port_raises(self):
        """Missing destination_port raises ValueError."""
        route = RouteSpec(
            origin_country="Australia",
            destination_country="India",
            destination_port="",
        )

        with pytest.raises(ValueError, match="destination_port"):
            route.validate()


class TestCargoSpecContract:
    """Tests for cargo specification validation."""

    def test_valid_cargo_spec(self):
        """Valid cargo spec passes validation."""
        cargo = CargoSpec(
            commodity_type="Iron Ore",
            weight_tons=50000,
        )

        assert cargo.validate() is True

    def test_missing_commodity_type_raises(self):
        """Missing commodity_type raises ValueError."""
        cargo = CargoSpec(
            commodity_type="",
        )

        with pytest.raises(ValueError, match="commodity_type"):
            cargo.validate()

    def test_optional_weight_missing_ok(self):
        """Optional weight_tons can be None."""
        cargo = CargoSpec(
            commodity_type="Iron Ore",
            weight_tons=None,
        )

        assert cargo.validate() is True


class TestRuleResultContract:
    """Tests for rule result contract."""

    def test_rule_result_pass_status(self):
        """RuleResult with PASS status."""
        result = RuleResult(
            rule_id="test_rule",
            description="Test",
            status="PASS",
            reason="All checks passed",
        )

        assert result.is_pass() is True
        assert result.is_fail() is False
        assert result.is_unavailable() is False

    def test_rule_result_fail_status(self):
        """RuleResult with FAIL status."""
        result = RuleResult(
            rule_id="test_rule",
            description="Test",
            status="FAIL",
            reason="Check failed",
        )

        assert result.is_pass() is False
        assert result.is_fail() is True
        assert result.is_unavailable() is False

    def test_rule_result_unavailable_status(self):
        """RuleResult with DATA_UNAVAILABLE status."""
        result = RuleResult(
            rule_id="test_rule",
            description="Test",
            status="DATA_UNAVAILABLE",
            reason="Data not available",
        )

        assert result.is_pass() is False
        assert result.is_fail() is False
        assert result.is_unavailable() is True


class TestFeasibilityResultContract:
    """Tests for feasibility result output contract."""

    def test_feasibility_result_to_dict(self):
        """FeasibilityResult converts to dict."""
        result = FeasibilityResult(
            feasibility_status="FEASIBLE",
            vessel_id="V001",
            origin="Australia",
            destination="Paradip SEA",
            destination_country="India",
            cargo_type="Iron Ore",
            violated_constraints=[],
            unavailable_constraints=[],
            evaluated_constraints=["vessel_cargo_compatibility"],
            explanation="All checks passed",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["feasibility_status"] == "FEASIBLE"
        assert result_dict["vessel_id"] == "V001"
        assert result_dict["origin"] == "Australia"
        assert result_dict["cargo_type"] == "Iron Ore"
        assert "timestamp" in result_dict
        assert "service_version" in result_dict

    def test_feasibility_result_all_fields_present(self):
        """All required fields present in FeasibilityResult."""
        result = FeasibilityResult(
            feasibility_status="INFEASIBLE",
            vessel_id=None,
            origin="Test",
            destination="Test",
            destination_country="Test",
            cargo_type="Iron Ore",
            violated_constraints=["rule1"],
        )

        result_dict = result.to_dict()
        required_fields = [
            "feasibility_status",
            "vessel_id",
            "origin",
            "destination",
            "destination_country",
            "cargo_type",
            "violated_constraints",
            "unavailable_constraints",
            "evaluated_constraints",
            "explanation",
            "detailed_results",
            "data_scope_version",
            "timestamp",
            "service_version",
        ]

        for field in required_fields:
            assert field in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
