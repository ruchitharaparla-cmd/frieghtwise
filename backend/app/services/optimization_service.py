from typing import Optional


COST_WEIGHT = 0.40
RISK_WEIGHT = 0.20
DELAY_WEIGHT = 0.15
FREIGHT_WEIGHT = 0.10
PORT_WEIGHT = 0.10
ARRIVAL_WEIGHT = 0.05


def normalize_lower_better(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Convert a value to a 0-100 penalty score.
    Lower original value = better.
    """

    if maximum == minimum:
        return 0.0

    return ((value - minimum) / (maximum - minimum)) * 100


def normalize_higher_better(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Convert a value to a 0-100 penalty score.
    Higher original value = better.
    """

    if maximum == minimum:
        return 0.0

    return ((maximum - value) / (maximum - minimum)) * 100


def calculate_option_score(
    total_landed_cost: Optional[float],
    overall_risk: Optional[float],
    expected_delay_hours: Optional[float],
    freight_rate: Optional[float],
    port_suitability_score: Optional[float],
    arrival_feasibility_score: Optional[float],
    cost_min: float,
    cost_max: float,
    delay_min: float,
    delay_max: float,
    freight_min: float,
    freight_max: float,
) -> Optional[float]:

    required_values = [
        total_landed_cost,
        overall_risk,
        expected_delay_hours,
        freight_rate,
        port_suitability_score,
        arrival_feasibility_score,
    ]

    if any(value is None for value in required_values):
        return None

    cost_score = normalize_lower_better(
        total_landed_cost,
        cost_min,
        cost_max,
    )

    risk_score = max(
        0.0,
        min(100.0, overall_risk),
    )

    delay_score = normalize_lower_better(
        expected_delay_hours,
        delay_min,
        delay_max,
    )

    freight_score = normalize_lower_better(
        freight_rate,
        freight_min,
        freight_max,
    )

    port_score = max(
        0.0,
        min(100.0, 100.0 - port_suitability_score),
    )

    arrival_score = max(
        0.0,
        min(100.0, 100.0 - arrival_feasibility_score),
    )

    final_score = (
        cost_score * COST_WEIGHT
        + risk_score * RISK_WEIGHT
        + delay_score * DELAY_WEIGHT
        + freight_score * FREIGHT_WEIGHT
        + port_score * PORT_WEIGHT
        + arrival_score * ARRIVAL_WEIGHT
    )

    return round(final_score, 2)


def rank_options(options: list[dict]) -> list[dict]:
    """
    Rank feasible vessel-port options.

    Lower final score = better option.
    """

    feasible_options = [
        option
        for option in options
        if option.get("feasible", False)
    ]

    if not feasible_options:
        return []

    costs = [
        option["total_landed_cost"]
        for option in feasible_options
        if option.get("total_landed_cost") is not None
    ]

    delays = [
        option["expected_delay_hours"]
        for option in feasible_options
        if option.get("expected_delay_hours") is not None
    ]

    freight_rates = [
        option["freight_rate"]
        for option in feasible_options
        if option.get("freight_rate") is not None
    ]

    if (
        len(costs) != len(feasible_options)
        or len(delays) != len(feasible_options)
        or len(freight_rates) != len(feasible_options)
    ):
        return []

    if any(
        option.get("overall_risk") is None
        or option.get("port_suitability_score") is None
        or option.get("arrival_feasibility_score") is None
        for option in feasible_options
    ):
        return []

    cost_min = min(costs)
    cost_max = max(costs)

    delay_min = min(delays)
    delay_max = max(delays)

    freight_min = min(freight_rates)
    freight_max = max(freight_rates)

    scored_options = []

    for option in feasible_options:
        scored_option = option.copy()

        scored_option["score"] = calculate_option_score(
            total_landed_cost=option.get("total_landed_cost"),
            overall_risk=option.get("overall_risk"),
            expected_delay_hours=option.get("expected_delay_hours"),
            freight_rate=option.get("freight_rate"),
            port_suitability_score=option.get(
                "port_suitability_score"
            ),
            arrival_feasibility_score=option.get(
                "arrival_feasibility_score"
            ),
            cost_min=cost_min,
            cost_max=cost_max,
            delay_min=delay_min,
            delay_max=delay_max,
            freight_min=freight_min,
            freight_max=freight_max,
        )

        scored_options.append(scored_option)

    scored_options.sort(
        key=lambda option: option["score"]
        if option["score"] is not None
        else float("inf")
    )

    for rank, option in enumerate(scored_options, start=1):
        option["rank"] = rank

    return scored_options


def choose_strategy(
    best_option: Optional[dict],
    forecast_direction: Optional[str] = None,
) -> str:

    if best_option is None:
        return "WAIT"

    if best_option.get("port_changed"):
        return "ALTERNATIVE_PORT"

    if best_option.get("vessel_changed"):
        return "ALTERNATIVE_VESSEL"

    if forecast_direction == "DOWN":
        return "WAIT"

    return "BOOK_NOW"