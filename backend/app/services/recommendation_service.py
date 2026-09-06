from typing import Optional

from app.services.optimization_service import (
    choose_strategy,
    rank_options,
)


def generate_recommendation(
    options: list[dict],
    forecast_direction: Optional[str] = None,
):
    feasible_options = [
        option
        for option in options
        if option.get("feasible", False)
    ]

    if not feasible_options:
        return {
            "strategy": "WAIT",
            "vessel_id": None,
            "port_id": None,
            "forecast": None,
            "cost": None,
            "risk": None,
            "reasons": [
                "No feasible vessel-port combination is available."
            ],
            "alternatives": [],
        }

    ranked_options = rank_options(feasible_options)

    best_option = ranked_options[0]

    strategy = choose_strategy(
        best_option=best_option,
        forecast_direction=forecast_direction,
    )

    reasons = []

    if best_option.get("total_landed_cost") is not None:
        reasons.append(
            "Selected option has the best calculated landed cost "
            "among feasible options."
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

    alternatives = []

    for option in ranked_options[1:]:
        alternatives.append(
            {
                "rank": option.get("rank"),
                "vessel_id": option.get("vessel_id"),
                "port_id": option.get("port_id"),
                "total_landed_cost": option.get("total_landed_cost"),
                "overall_risk": option.get("overall_risk"),
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