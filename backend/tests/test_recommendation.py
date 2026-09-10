from datetime import date

from app.schemas.recommendation import RecommendationRequest
from app.services.cost_service import calculate_cost
from app.services.optimization_service import rank_options


def test_recommendation_request_requires_charter_duration():
    """
    The current freight forecast is expressed as USD/day.
    Therefore charter duration is required to calculate voyage freight cost.
    """

    request_data = {
        "cargo_type": "coal",
        "quantity_tonnes": 75000,
        "origin_country": "Australia",
        "destination_region": "East Coast India",
        "arrival_date": date(2026, 9, 20),
    }

    try:
        RecommendationRequest(**request_data)
        assert False, "Expected validation error for missing charter duration"
    except Exception:
        pass


def test_recommendation_request_accepts_valid_charter_duration():
    request = RecommendationRequest(
        cargo_type="coal",
        quantity_tonnes=75000,
        origin_country="Australia",
        destination_region="East Coast India",
        arrival_date=date(2026, 9, 20),
        charter_duration_days=20,
    )

    assert request.charter_duration_days == 20


def test_usd_per_day_freight_cost_uses_voyage_duration():
    """
    USD/day must be multiplied by voyage duration,
    not by cargo quantity.
    """

    result = calculate_cost(
        quantity_tonnes=75000,
        freight_rate=9745.7509765625,
        bunker_cost=300000.0,
        port_cost=100000.0,
        expected_delay_hours=6.0,
        demurrage_rate_per_day=20000.0,
        freight_rate_unit="USD/day",
        voyage_duration_days=20,
    )

    assert result["freight_cost"] == 194915.01953125
    assert result["expected_demurrage"] == 5000.0
    assert result["total_landed_cost"] == 599915.01953125


def test_optimizer_prefers_lower_landed_cost():
    """
    When operational signals are equal, the lower-cost option
    should receive the better optimization score.
    """

    options = [
        {
            "feasible": True,
            "vessel_id": 1,
            "port_id": 1,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
        {
            "feasible": True,
            "vessel_id": 2,
            "port_id": 2,
            "total_landed_cost": 650000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
    ]

    ranked = rank_options(options)

    assert len(ranked) == 2
    assert ranked[0]["vessel_id"] == 1
    assert ranked[0]["port_id"] == 1
    assert ranked[0]["score"] < ranked[1]["score"]


def test_optimizer_prefers_lower_risk_when_cost_is_equal():
    options = [
        {
            "feasible": True,
            "vessel_id": 1,
            "port_id": 1,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
        {
            "feasible": True,
            "vessel_id": 2,
            "port_id": 2,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 40.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
    ]

    ranked = rank_options(options)

    assert len(ranked) == 2
    assert ranked[0]["vessel_id"] == 1
    assert ranked[0]["score"] < ranked[1]["score"]


def test_optimizer_prefers_lower_delay_when_cost_and_risk_are_equal():
    options = [
        {
            "feasible": True,
            "vessel_id": 1,
            "port_id": 1,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 4.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
        {
            "feasible": True,
            "vessel_id": 2,
            "port_id": 2,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 10.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
    ]

    ranked = rank_options(options)

    assert len(ranked) == 2
    assert ranked[0]["vessel_id"] == 1
    assert ranked[0]["score"] < ranked[1]["score"]


def test_optimizer_prefers_better_arrival_feasibility():
    options = [
        {
            "feasible": True,
            "vessel_id": 1,
            "port_id": 1,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
        {
            "feasible": True,
            "vessel_id": 2,
            "port_id": 2,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 40.0,
        },
    ]

    ranked = rank_options(options)

    assert len(ranked) == 2
    assert ranked[0]["vessel_id"] == 1
    assert ranked[0]["score"] < ranked[1]["score"]


def test_optimizer_assigns_sequential_ranks():
    options = [
        {
            "feasible": True,
            "vessel_id": 1,
            "port_id": 1,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
        {
            "feasible": True,
            "vessel_id": 2,
            "port_id": 2,
            "total_landed_cost": 650000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
    ]

    ranked = rank_options(options)

    assert ranked[0]["rank"] == 1
    assert ranked[1]["rank"] == 2


def test_optimizer_ignores_infeasible_options():
    options = [
        {
            "feasible": True,
            "vessel_id": 1,
            "port_id": 1,
            "total_landed_cost": 600000.0,
            "freight_rate": 10000.0,
            "overall_risk": 10.0,
            "expected_delay_hours": 6.0,
            "congestion_score": 20.0,
            "arrival_feasibility_score": 100.0,
        },
        {
            "feasible": False,
            "vessel_id": 2,
            "port_id": 2,
            "total_landed_cost": None,
            "freight_rate": None,
            "rejection_reasons": [
                "Vessel dimensions exceed port limits."
            ],
        },
    ]

    ranked = rank_options(options)

    assert len(ranked) == 1
    assert ranked[0]["vessel_id"] == 1