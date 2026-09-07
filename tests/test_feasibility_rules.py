"""
Unit tests for FreightWise Stage 4 constraint rules.

Tests individual rule implementations, pass/fail conditions, and DATA_UNAVAILABLE behavior.
"""

import pytest
from src.feasibility.contracts import (
    VesselSpec,
    PortSpec,
    RouteSpec,
    CargoSpec,
)
from src.feasibility.data_loader import ConstraintDataLoader
from src.feasibility.rules import (
    VesselTypeCargoCompatibilityRule,
    VesselMaintenanceStatusRule,
    VesselDraftPortCompatibilityRule,
    PortKnownInDataRule,
    CargoTypesSupportedRule,
    RouteValidityRule,
)


class TestVesselTypeCargoCompatibilityRule:
    """Tests for vessel type ↔ cargo compatibility rule."""

    @pytest.fixture
    def rule(self):
        return VesselTypeCargoCompatibilityRule()

    @pytest.fixture
    def data_loader(self):
        return ConstraintDataLoader()

    def test_bulk_carrier_iron_ore_pass(self, rule, data_loader):
        """Bulk Carrier can carry Iron Ore."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_pass()
        assert "Bulk Carrier" in result.reason

    def test_tanker_iron_ore_fail(self, rule, data_loader):
        """Tanker cannot carry Iron Ore."""
        vessel = VesselSpec(ship_type="Tanker", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_fail()

    def test_missing_ship_type_unavailable(self, rule, data_loader):
        """Missing ship_type returns DATA_UNAVAILABLE."""
        vessel = VesselSpec(ship_type="", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()

    def test_unsupported_commodity_unavailable(self, rule, data_loader):
        """Unsupported commodity returns DATA_UNAVAILABLE."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Exotic Mineral XYZ")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()


class TestVesselMaintenanceStatusRule:
    """Tests for vessel maintenance status rule."""

    @pytest.fixture
    def rule(self):
        return VesselMaintenanceStatusRule()

    @pytest.fixture
    def data_loader(self):
        return ConstraintDataLoader()

    def test_good_maintenance_pass(self, rule, data_loader):
        """Maintenance status 'Good' passes."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_pass()

    def test_fair_maintenance_pass(self, rule, data_loader):
        """Maintenance status 'Fair' passes (with warning)."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Fair")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_pass()
        assert result.severity == "WARNING"

    def test_critical_maintenance_fail(self, rule, data_loader):
        """Maintenance status 'Critical' fails."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Critical")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_fail()
        assert "CRITICAL" in result.reason

    def test_missing_maintenance_unavailable(self, rule, data_loader):
        """Missing maintenance status returns DATA_UNAVAILABLE."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()


class TestVesselDraftPortCompatibilityRule:
    """Tests for vessel draft vs port depth rule."""

    @pytest.fixture
    def rule(self):
        return VesselDraftPortCompatibilityRule()

    @pytest.fixture
    def data_loader(self):
        return ConstraintDataLoader()

    def test_draft_within_limit_pass(self, rule, data_loader):
        """Vessel draft within port limit passes."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good", draft_meters=10.0)
        port = PortSpec(
            port_name="TestPort",
            country="Denmark",
            max_channel_depth_meters=12.0
        )
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_pass()

    def test_draft_exceeds_limit_fail(self, rule, data_loader):
        """Vessel draft exceeding port limit fails."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good", draft_meters=14.0)
        port = PortSpec(
            port_name="TestPort",
            country="Denmark",
            max_channel_depth_meters=12.0
        )
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_fail()

    def test_indian_port_unavailable(self, rule, data_loader):
        """Indian port returns DATA_UNAVAILABLE (no fabricated specs)."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good", draft_meters=10.0)
        port = PortSpec(
            port_name="Paradip SEA",
            country="India",
        )
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()
        assert "India" in result.reason or "verified" in result.reason.lower()

    def test_missing_vessel_draft_unavailable(self, rule, data_loader):
        """Missing vessel draft returns DATA_UNAVAILABLE."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good", draft_meters=None)
        port = PortSpec(
            port_name="TestPort",
            country="Denmark",
            max_channel_depth_meters=12.0
        )
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()


class TestCargoTypeSupportedRule:
    """Tests for cargo type support rule."""

    @pytest.fixture
    def rule(self):
        return CargoTypesSupportedRule()

    @pytest.fixture
    def data_loader(self):
        return ConstraintDataLoader()

    def test_iron_ore_supported_pass(self, rule, data_loader):
        """Iron Ore is supported."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_pass()

    def test_unsupported_commodity_unavailable(self, rule, data_loader):
        """Unsupported commodity returns DATA_UNAVAILABLE."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(origin_country="Test", destination_country="Test", destination_port="Test")
        cargo = CargoSpec(commodity_type="Flying Unicorn Dust")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()


class TestRouteValidityRule:
    """Tests for route validity rule."""

    @pytest.fixture
    def rule(self):
        return RouteValidityRule()

    @pytest.fixture
    def data_loader(self):
        return ConstraintDataLoader()

    def test_valid_route_pass(self, rule, data_loader):
        """Valid route structure passes."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(
            origin_country="Australia",
            destination_country="India",
            destination_port="Paradip SEA"
        )
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_pass()

    def test_missing_origin_unavailable(self, rule, data_loader):
        """Missing origin country returns DATA_UNAVAILABLE."""
        vessel = VesselSpec(ship_type="Bulk Carrier", maintenance_status="Good")
        port = PortSpec(port_name="Test", country="Test")
        route = RouteSpec(
            origin_country="",
            destination_country="India",
            destination_port="Paradip SEA"
        )
        cargo = CargoSpec(commodity_type="Iron Ore")

        result = rule.evaluate(vessel, port, route, cargo, data_loader)

        assert result.is_unavailable()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
