from app.services.optimization_service import (
    choose_strategy,
    rank_options,
)


def generate_recommendation(options, forecast_direction=None):

    feasible_options = [
        option
        for option in options
        if option.get("feasible", False)
    ]

    # ---------------------------------------------------------
    # NO FEASIBLE OPTIONS
    # ---------------------------------------------------------

    if not feasible_options:

        reasons = []

        for option in options:
            for reason in option.get(
                "rejection_reasons",
                [],
            ):
                if reason not in reasons:
                    reasons.append(reason)

        if not reasons:
            reasons = [
                "No feasible vessel-port combination is available."
            ]

        return {
            "strategy": "WAIT",
            "vessel_id": None,
            "port_id": None,
            "forecast": None,
            "cost": None,
            "risk": None,
            "score": None,
            "score_breakdown": {},
            "reasons": reasons,
            "alternatives": [],
        }

    # ---------------------------------------------------------
    # RANK FEASIBLE OPTIONS
    # ---------------------------------------------------------

    ranked_options = rank_options(
        feasible_options
    )

    if not ranked_options:
        return {
            "strategy": "WAIT",
            "vessel_id": None,
            "port_id": None,
            "forecast": None,
            "cost": None,
            "risk": None,
            "score": None,
            "score_breakdown": {},
            "reasons": [
                "Insufficient data is available to rank the feasible options."
            ],
            "alternatives": [],
        }

    # ---------------------------------------------------------
    # BEST OPTION
    # ---------------------------------------------------------

    best_option = ranked_options[0]

    strategy = choose_strategy(
        best_option,
        forecast_direction,
    )

    reasons = []

    # ---------------------------------------------------------
    # COST EXPLANATION
    # ---------------------------------------------------------

    best_cost = best_option.get(
        "total_landed_cost"
    )

    tied_on_cost = [
        option
        for option in ranked_options
        if option.get("total_landed_cost") == best_cost
    ]

    if best_cost is not None:

        if len(tied_on_cost) == 1:
            reasons.append(
                "Selected option has the lowest calculated landed cost "
                "among feasible options."
            )
        else:
            reasons.append(
                "Selected option is tied for the lowest calculated landed "
                "cost; additional operational signals were used to rank it."
            )

    # ---------------------------------------------------------
    # OPERATIONAL RISK
    # ---------------------------------------------------------

    if best_option.get("overall_risk") is not None:
        reasons.append(
            f"Calculated operational risk is "
            f"{best_option['overall_risk']:.2f}."
        )

    # ---------------------------------------------------------
    # ARRIVAL FEASIBILITY
    #
    # Higher score = better.
    # ---------------------------------------------------------

    arrival_score = best_option.get(
        "arrival_feasibility_score"
    )

    if arrival_score is not None:

        if arrival_score >= 80:
            arrival_level = "excellent"
        elif arrival_score >= 60:
            arrival_level = "strong"
        elif arrival_score >= 40:
            arrival_level = "moderate"
        else:
            arrival_level = "limited"

        reasons.append(
            f"Vessel-port dimensional feasibility is "
            f"{arrival_level} with a score of "
            f"{arrival_score:.2f}."
        )

    # ---------------------------------------------------------
    # DELAY
    # ---------------------------------------------------------

    if best_option.get(
        "expected_delay_hours"
    ) is not None:
        reasons.append(
            f"Expected delay is "
            f"{best_option['expected_delay_hours']:.1f} hours."
        )

    # ---------------------------------------------------------
    # MISSING SIGNALS
    # ---------------------------------------------------------

    unavailable_signals = best_option.get(
        "unavailable_signals",
        [],
    )

    signal_labels = {
        "risk": "operational risk",
        "delay": "delay",
        "congestion": "port congestion",
        "arrival_feasibility": "arrival feasibility",
    }

    readable_missing_signals = [
        signal_labels.get(
            signal,
            signal,
        )
        for signal in unavailable_signals
    ]

    if readable_missing_signals:

        if len(readable_missing_signals) == 1:
            missing_text = readable_missing_signals[0]
        else:
            missing_text = ", ".join(
                readable_missing_signals
            )

        reasons.append(
            "The recommendation was ranked without "
            f"{missing_text} data because those signals are unavailable."
        )

    # ---------------------------------------------------------
    # WAIT STRATEGY
    # ---------------------------------------------------------

    if strategy == "WAIT":
        reasons.append(
            "Freight conditions indicate waiting may be preferable."
        )

    # ---------------------------------------------------------
    # FORECAST CONFIDENCE
    # ---------------------------------------------------------

    forecast = best_option.get(
        "forecast"
    )

    if forecast:

        confidence = forecast.get(
            "confidence"
        )

        if (
            confidence is not None
            and confidence < 0.50
        ):
            reasons.append(
                "Forecast confidence is low; recommendation "
                "should be treated cautiously."
            )

    # ---------------------------------------------------------
    # ALTERNATIVES
    # ---------------------------------------------------------

    alternatives = []

    for option in ranked_options[1:]:

        alternatives.append(
            {
                "rank": option.get(
                    "rank"
                ),
                "vessel_id": option.get(
                    "vessel_id"
                ),
                "port_id": option.get(
                    "port_id"
                ),

                # Optimization result
                "score": option.get(
                    "score"
                ),
                "score_breakdown": option.get(
                    "score_breakdown",
                    {},
                ),

                # Cost / risk / operational signals
                "total_landed_cost": option.get(
                    "total_landed_cost"
                ),
                "overall_risk": option.get(
                    "overall_risk"
                ),
                "expected_delay_hours": option.get(
                    "expected_delay_hours"
                ),
                "arrival_feasibility_score": option.get(
                    "arrival_feasibility_score"
                ),

                # Data availability
                "unavailable_signals": option.get(
                    "unavailable_signals",
                    [],
                ),

                # Rejection information
                "rejection_reasons": option.get(
                    "rejection_reasons",
                    [],
                ),
            }
        )

    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    return {
        "strategy": strategy,

        "vessel_id": best_option.get(
            "vessel_id"
        ),

        "port_id": best_option.get(
            "port_id"
        ),

        # Forecast result
        "forecast": best_option.get(
            "forecast"
        ),

        # Cost result
        "cost": best_option.get(
            "cost"
        ),

        # Risk result
        "risk": best_option.get(
            "risk"
        ),

        # Overall optimization score
        "score": best_option.get(
            "score"
        ),

        # Contribution of each decision factor
        "score_breakdown": best_option.get(
            "score_breakdown",
            {},
        ),

        # Human-readable explanation
        "reasons": reasons,

        # Ranked alternatives
        "alternatives": alternatives,
    }