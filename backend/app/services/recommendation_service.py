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

    # No feasible options
    if not feasible_options:

        reasons = []

        for option in options:
            for reason in option.get("rejection_reasons", []):
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
            "reasons": reasons,
            "alternatives": [],
        }

    # Try ranking feasible options
    ranked_options = rank_options(feasible_options)

    # Feasible options exist but cannot be ranked
    if not ranked_options:
        return {
            "strategy": "WAIT",
            "vessel_id": None,
            "port_id": None,
            "forecast": None,
            "cost": None,
            "risk": None,
            "reasons": [
                "Insufficient data is available to rank the feasible options."
            ],
            "alternatives": [],
        }

    best_option = ranked_options[0]

    strategy = choose_strategy(
        best_option,
        forecast_direction,
    )

    reasons = []

    if best_option.get("total_landed_cost") is not None:
        reasons.append(
            "Selected option has the best calculated landed cost among feasible options."
        )

    if best_option.get("overall_risk") is not None:
        reasons.append(
            f"Calculated operational risk is "
            f"{best_option['overall_risk']:.2f}."
        )

    if best_option.get("expected_delay_hours") is not None:
        reasons.append(
            f"Expected delay is "
            f"{best_option['expected_delay_hours']:.1f} hours."
        )

    if strategy == "WAIT":
        reasons.append(
            "Freight conditions indicate waiting may be preferable."
        )

    forecast = best_option.get("forecast")

    if forecast:
        confidence = forecast.get("confidence")

        if confidence is not None and confidence < 0.50:
            reasons.append(
                "Forecast confidence is low; recommendation should be treated cautiously."
            )

    alternatives = []

    for option in ranked_options[1:]:
        alternatives.append(
            {
                "rank": option.get("rank"),
                "vessel_id": option.get("vessel_id"),
                "port_id": option.get("port_id"),
                "total_landed_cost": option.get(
                    "total_landed_cost"
                ),
                "overall_risk": option.get(
                    "overall_risk"
                ),
                "rejection_reasons": option.get(
                    "rejection_reasons",
                    [],
                ),
            }
        )

    return {
        "strategy": strategy,
        "vessel_id": best_option.get("vessel_id"),
        "port_id": best_option.get("port_id"),
        "forecast": best_option.get("forecast"),
        "cost": best_option.get("cost"),
        "risk": best_option.get("risk"),
        "reasons": reasons,
        "alternatives": alternatives,
    }