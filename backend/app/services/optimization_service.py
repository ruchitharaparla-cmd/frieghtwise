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
    congestion_score: Optional[float],
    arrival_feasibility_score: Optional[float],
    cost_min: float,
    cost_max: float,
    delay_min: float,
    delay_max: float,
    freight_min: float,
    freight_max: float,
) -> Optional[dict]:
    """
    Calculate a weighted option score using only available signals.

    Lower final score = better option.

    Missing signals are excluded and the remaining weights are
    renormalized. No missing value is fabricated.

    Returns:
        {
            "score": float,
            "score_breakdown": {
                "cost": float,
                "risk": float,
                "delay": float,
                "freight": float,
                "congestion": float,
                "arrival_feasibility": float
            }
        }
    """

    components = []

    # ---------------------------------------------------------
    # COST
    # ---------------------------------------------------------
    if total_landed_cost is not None:
        cost_score = normalize_lower_better(
            total_landed_cost,
            cost_min,
            cost_max,
        )

        components.append(
            ("cost", cost_score, COST_WEIGHT)
        )

    # ---------------------------------------------------------
    # RISK
    # ---------------------------------------------------------
    if overall_risk is not None:
        risk_score = max(
            0.0,
            min(100.0, overall_risk),
        )

        components.append(
            ("risk", risk_score, RISK_WEIGHT)
        )

    # ---------------------------------------------------------
    # DELAY
    # ---------------------------------------------------------
    if expected_delay_hours is not None:
        delay_score = normalize_lower_better(
            expected_delay_hours,
            delay_min,
            delay_max,
        )

        components.append(
            ("delay", delay_score, DELAY_WEIGHT)
        )

    # ---------------------------------------------------------
    # FREIGHT RATE
    # ---------------------------------------------------------
    if freight_rate is not None:
        freight_score = normalize_lower_better(
            freight_rate,
            freight_min,
            freight_max,
        )

        components.append(
            ("freight", freight_score, FREIGHT_WEIGHT)
        )

    # ---------------------------------------------------------
    # PORT CONGESTION
    # ---------------------------------------------------------
    # Congestion score:
    # 20 = LOW
    # 50 = MEDIUM
    # 80 = HIGH
    #
    # Lower congestion = better option.
    if congestion_score is not None:
        congestion_score = max(
            0.0,
            min(
                100.0,
                congestion_score,
            ),
        )

        components.append(
            ("congestion", congestion_score, PORT_WEIGHT)
        )

    # ---------------------------------------------------------
    # ARRIVAL FEASIBILITY
    # ---------------------------------------------------------
    if arrival_feasibility_score is not None:
        arrival_score = max(
            0.0,
            min(
                100.0,
                100.0 - arrival_feasibility_score,
            ),
        )

        components.append(
            (
                "arrival_feasibility",
                arrival_score,
                ARRIVAL_WEIGHT,
            )
        )

    # ---------------------------------------------------------
    # NO USABLE SIGNALS
    # ---------------------------------------------------------
    if not components:
        return None

    # ---------------------------------------------------------
    # RENORMALIZE AVAILABLE WEIGHTS
    # ---------------------------------------------------------
    total_weight = sum(
        weight
        for _, _, weight in components
    )

    if total_weight <= 0:
        return None

    # ---------------------------------------------------------
    # CALCULATE WEIGHTED CONTRIBUTIONS
    # ---------------------------------------------------------
    score_breakdown = {}

    final_score = 0.0

    for name, raw_score, weight in components:
        normalized_weight = weight / total_weight

        contribution = (
            raw_score * normalized_weight
        )

        score_breakdown[name] = round(
            contribution,
            2,
        )

        final_score += contribution

    return {
        "score": round(final_score, 2),
        "score_breakdown": score_breakdown,
    }


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
        - congestion_score
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

        score_result = calculate_option_score(
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
            congestion_score=option.get(
                "congestion_score"
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

        if score_result is not None:
            scored_option["score"] = (
                score_result["score"]
            )

            scored_option["score_breakdown"] = (
                score_result["score_breakdown"]
            )
        else:
            scored_option["score"] = None
            scored_option["score_breakdown"] = {}

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

        if option.get("congestion_score") is None:
            unavailable_signals.append(
                "congestion"
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
