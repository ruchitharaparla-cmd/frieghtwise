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
    """
    Calculate a weighted option score using only available signals.

    Lower final score = better option.

    Missing signals are excluded and the remaining weights are
    renormalized. No missing value is fabricated.
    """

    components = []

    # ---------------------------------------------------------
    # COST
    # ---------------------------------------------------------
    if total_landed_cost is not None:
        components.append(
            (
                normalize_lower_better(
                    total_landed_cost,
                    cost_min,
                    cost_max,
                ),
                COST_WEIGHT,
            )
        )

    # ---------------------------------------------------------
    # RISK
    # ---------------------------------------------------------
    if overall_risk is not None:
        components.append(
            (
                max(
                    0.0,
                    min(100.0, overall_risk),
                ),
                RISK_WEIGHT,
            )
        )

    # ---------------------------------------------------------
    # DELAY
    # ---------------------------------------------------------
    if expected_delay_hours is not None:
        components.append(
            (
                normalize_lower_better(
                    expected_delay_hours,
                    delay_min,
                    delay_max,
                ),
                DELAY_WEIGHT,
            )
        )

    # ---------------------------------------------------------
    # FREIGHT RATE
    # ---------------------------------------------------------
    if freight_rate is not None:
        components.append(
            (
                normalize_lower_better(
                    freight_rate,
                    freight_min,
                    freight_max,
                ),
                FREIGHT_WEIGHT,
            )
        )

    # ---------------------------------------------------------
    # PORT SUITABILITY
    # ---------------------------------------------------------
    if port_suitability_score is not None:
        components.append(
            (
                max(
                    0.0,
                    min(
                        100.0,
                        100.0 - port_suitability_score,
                    ),
                ),
                PORT_WEIGHT,
            )
        )

    # ---------------------------------------------------------
    # ARRIVAL FEASIBILITY
    # ---------------------------------------------------------
    if arrival_feasibility_score is not None:
        components.append(
            (
                max(
                    0.0,
                    min(
                        100.0,
                        100.0 - arrival_feasibility_score,
                    ),
                ),
                ARRIVAL_WEIGHT,
            )
        )

    # No usable signals
    if not components:
        return None

    # ---------------------------------------------------------
    # RENORMALIZE AVAILABLE WEIGHTS
    # ---------------------------------------------------------
    total_weight = sum(
        weight
        for _, weight in components
    )

    if total_weight <= 0:
        return None

    final_score = sum(
        score * (weight / total_weight)
        for score, weight in components
    )

    return round(final_score, 2)


def rank_options(
    options: list[dict],
) -> list[dict]:
    """
    Rank feasible vessel-port options.

    Required for economic ranking:
        - total_landed_cost
        - freight_rate

    Optional signals:
        - overall_risk
        - expected_delay_hours
        - port_suitability_score
        - arrival_feasibility_score

    Missing optional signals are excluded from the score and
    the remaining weights are renormalized.

    Lower final score = better option.
    """

    feasible_options = [
        option
        for option in options
        if option.get("feasible", False)
    ]

    if not feasible_options:
        return []

    # ---------------------------------------------------------
    # REQUIRED ECONOMIC DATA
    # ---------------------------------------------------------
    required_fields = [
        "total_landed_cost",
        "freight_rate",
    ]

    for option in feasible_options:
        for field in required_fields:
            if option.get(field) is None:
                return []

    # ---------------------------------------------------------
    # NORMALIZATION DATA
    # ---------------------------------------------------------
    costs = [
        option["total_landed_cost"]
        for option in feasible_options
    ]

    freight_rates = [
        option["freight_rate"]
        for option in feasible_options
    ]

    delays = [
        option["expected_delay_hours"]
        for option in feasible_options
        if option.get("expected_delay_hours") is not None
    ]

    cost_min = min(costs)
    cost_max = max(costs)

    freight_min = min(freight_rates)
    freight_max = max(freight_rates)

    if delays:
        delay_min = min(delays)
        delay_max = max(delays)
    else:
        delay_min = 0.0
        delay_max = 0.0

    scored_options = []

    # ---------------------------------------------------------
    # SCORE EACH OPTION
    # ---------------------------------------------------------
    for option in feasible_options:

        scored_option = option.copy()

        scored_option["score"] = calculate_option_score(
            total_landed_cost=option.get(
                "total_landed_cost"
            ),
            overall_risk=option.get(
                "overall_risk"
            ),
            expected_delay_hours=option.get(
                "expected_delay_hours"
            ),
            freight_rate=option.get(
                "freight_rate"
            ),
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

        # -----------------------------------------------------
        # TRACK MISSING SIGNALS
        # -----------------------------------------------------
        unavailable_signals = []

        if option.get("overall_risk") is None:
            unavailable_signals.append(
                "risk"
            )

        if option.get("expected_delay_hours") is None:
            unavailable_signals.append(
                "delay"
            )

        if option.get("port_suitability_score") is None:
            unavailable_signals.append(
                "port_suitability"
            )

        if option.get("arrival_feasibility_score") is None:
            unavailable_signals.append(
                "arrival_feasibility"
            )

        scored_option["unavailable_signals"] = (
            unavailable_signals
        )

        scored_options.append(
            scored_option
        )

    # ---------------------------------------------------------
    # REMOVE OPTIONS WITH NO SCORE
    # ---------------------------------------------------------
    scored_options = [
        option
        for option in scored_options
        if option.get("score") is not None
    ]

    if not scored_options:
        return []

    # ---------------------------------------------------------
    # SORT
    # ---------------------------------------------------------
    scored_options.sort(
        key=lambda option: option["score"]
    )

    # ---------------------------------------------------------
    # ASSIGN RANK
    # ---------------------------------------------------------
    for rank, option in enumerate(
        scored_options,
        start=1,
    ):
        option["rank"] = rank

    return scored_options


def choose_strategy(
    best_option: Optional[dict],
    forecast_direction: Optional[str] = None,
) -> str:
    """
    Select the chartering strategy.
    """

    if best_option is None:
        return "WAIT"

    if best_option.get("port_changed"):
        return "ALTERNATIVE_PORT"

    if best_option.get("vessel_changed"):
        return "ALTERNATIVE_VESSEL"

    if forecast_direction == "DOWN":
        return "WAIT"

    return "BOOK_NOW"