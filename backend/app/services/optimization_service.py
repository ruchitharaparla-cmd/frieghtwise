from typing import Optional


def calculate_option_score(
    total_landed_cost: Optional[float],
    overall_risk: Optional[float],
    expected_delay_hours: Optional[float],
    freight_rate: Optional[float],
) -> Optional[float]:
    """
    Lower score = better option.

    Returns None when the required cost/risk information
    is insufficient for a reliable ranking.
    """

    if total_landed_cost is None:
        return None

    cost_score = total_landed_cost

    risk_score = overall_risk if overall_risk is not None else 50.0

    delay_score = (
        expected_delay_hours
        if expected_delay_hours is not None
        else 24.0
    )

    freight_score = (
        freight_rate
        if freight_rate is not None
        else 0.0
    )

    return (
        (cost_score * 0.60)
        + (risk_score * 1000 * 0.20)
        + (delay_score * 1000 * 0.15)
        + (freight_score * 1000 * 0.05)
    )


def rank_options(options: list[dict]) -> list[dict]:
    """
    Rank feasible options from best to worst.
    Options without a calculable score are placed last.
    """

    scored_options = []

    for option in options:
        score = calculate_option_score(
            total_landed_cost=option.get("total_landed_cost"),
            overall_risk=option.get("overall_risk"),
            expected_delay_hours=option.get("expected_delay_hours"),
            freight_rate=option.get("freight_rate"),
        )

        option["score"] = score
        scored_options.append(option)

    scored_options.sort(
        key=lambda option: (
            option["score"] is None,
            option["score"] if option["score"] is not None else float("inf"),
        )
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