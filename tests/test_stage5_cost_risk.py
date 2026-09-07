"""Focused contract tests for the isolated Stage 5 calculation engine."""

from src.delays.service import IndiaPortDataAbsentError
from src.stage5 import ProjectParameters, Stage5CalculationEngine


class FakeDelayService:
    def predict_turnaround(self, payload):
        return {
            "predicted_turnaround_hours": 48.5,
            "delay_risk_score": 0.25,
            "model_name": "fake-stage3-delay",
            "data_scope": "GLOBAL_VESSEL_DELAY",
        }


class FakeCongestionService:
    def predict_congestion(self, payload):
        return {
            "risk_probability": 0.4,
            "model_name": "fake-stage3-congestion",
            "data_scope": "GLOBAL_CONGESTION_PROXY",
        }


class IndiaBlockedCongestionService:
    def predict_congestion(self, payload):
        raise IndiaPortDataAbsentError("Indian port data is unavailable")


def complete_inputs():
    return {
        "quantity_tonnes": 1000,
        "freight_rate": 1.0,
        "bunker_cost": 200.0,
        "port_charges": 300.0,
        "expected_delay_hours": 24.0,
        "demurrage_rate_per_day": 240.0,
        "weather_context": {"risk_value": 0.2, "source": "historical weather"},
        "delay_input": {"voyage": "sample"},
        "congestion_input": {"port": "Shanghai"},
    }


def test_calculation_is_deterministic_and_has_component_metadata():
    engine = Stage5CalculationEngine(
        delay_service=FakeDelayService(),
        congestion_service=FakeCongestionService(),
    )
    first = engine.calculate(**complete_inputs())
    second = engine.calculate(**complete_inputs())

    assert first == second
    assert first["total_known_cost"] == 1740.0
    assert first["cost_completeness"] == "COMPLETE"
    assert first["cost_components"]["freight"]["status"] == "KNOWN"
    assert first["cost_components"]["freight"]["currency"] == "USD"
    for component in first["cost_components"].values():
        assert set(("name", "value", "unit", "currency", "status", "assumptions", "data_scope", "source")) <= set(component)


def test_missing_values_stay_none_and_never_become_zero():
    result = Stage5CalculationEngine().calculate(quantity_tonnes=1000, freight_rate=1.0)

    assert result["cost_components"]["bunker"]["value"] is None
    assert result["cost_components"]["bunker"]["status"] == "UNAVAILABLE_MISSING_INPUT"
    assert result["cost_components"]["port_charges"]["value"] is None
    assert result["total_known_cost"] == 1000.0
    assert result["cost_completeness"] == "PARTIAL"
    assert set(result["missing_cost_components"]) == {"bunker", "port_charges", "demurrage"}


def test_project_parameters_control_demurrage_and_are_labeled():
    parameters = ProjectParameters(hours_per_day=12.0, default_currency="EUR")
    result = Stage5CalculationEngine(project_parameters=parameters).calculate(
        quantity_tonnes=1,
        freight_rate=1,
        bunker_cost=1,
        port_charges=1,
        expected_delay_hours=12,
        demurrage_rate_per_day=120,
    )

    assert result["cost_components"]["demurrage"]["value"] == 120.0
    assert result["cost_components"]["demurrage"]["currency"] == "EUR"
    assert result["project_parameters"]["source_label"] == "project_parameters"


def test_stage3_provenance_and_global_scope_are_preserved():
    result = Stage5CalculationEngine(
        delay_service=FakeDelayService(),
        congestion_service=FakeCongestionService(),
    ).calculate(**complete_inputs())

    congestion = result["risk_components"]["congestion"]
    assert congestion["data_scope"] == "GLOBAL_CONGESTION_PROXY"
    assert congestion["source"]["model_name"] == "fake-stage3-congestion"
    assert result["risk_components"]["delay"]["source"]["model_name"] == "fake-stage3-delay"


def test_indian_port_congestion_remains_unavailable():
    result = Stage5CalculationEngine(
        congestion_service=IndiaBlockedCongestionService(),
    ).calculate(congestion_input={"port": "Paradip"})

    congestion = result["risk_components"]["congestion"]
    assert congestion["value"] is None
    assert congestion["status"].startswith("UNAVAILABLE_")
    assert congestion["data_scope"] == "GLOBAL_CONGESTION_PROXY"


def test_historical_weather_is_context_only_not_future_forecast():
    result = Stage5CalculationEngine().calculate(
        weather_context={"risk_value": 0.8, "source": "historical observation"},
    )

    weather = result["risk_components"]["weather"]
    assert weather["value"] == 0.8
    assert weather["status"] == "HISTORICAL_CONTEXT_ONLY"
    assert weather["data_scope"] == "HISTORICAL"
    assert "future numerical forecast" in weather["assumptions"][0]


def test_feasibility_status_is_separate_from_cost_completeness():
    class FeasibilityService:
        def check_feasibility(self, **payload):
            return {"feasibility_status": "FEASIBLE"}

    result = Stage5CalculationEngine(feasibility_service=FeasibilityService()).calculate(
        feasibility_input={"vessel": {}, "destination_port": "Paradip"},
    )

    assert result["feasibility"]["status"] == "FEASIBLE"
    assert result["cost_completeness"] == "PARTIAL"