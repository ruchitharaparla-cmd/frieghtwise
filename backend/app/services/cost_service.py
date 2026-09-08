from typing import Optional


def calculate_cost(
    quantity_tonnes: float,
    freight_rate: Optional[float],
    bunker_cost: Optional[float],
    port_cost: Optional[float],
    expected_delay_hours: Optional[float],
    demurrage_rate_per_day: Optional[float],
    freight_rate_unit: str = "USD/day",
    voyage_duration_days: Optional[float] = None,
):
    freight_cost = None
    expected_delay_cost = None
    expected_demurrage = None

    # ---------------------------------------------------------
    # Freight cost
    #
    # The production XGBoost model outputs a market freight
    # benchmark in USD/day.
    #
    # Therefore:
    #     freight cost = USD/day × voyage duration
    #
    # We deliberately do not multiply USD/day by cargo tonnes.
    # ---------------------------------------------------------
    if freight_rate is not None:
        if freight_rate_unit == "USD/day":
            if voyage_duration_days is not None:
                freight_cost = freight_rate * voyage_duration_days

        elif freight_rate_unit == "USD/tonne":
            freight_cost = quantity_tonnes * freight_rate

        else:
            raise ValueError(
                f"Unsupported freight rate unit: {freight_rate_unit}"
            )

    # ---------------------------------------------------------
    # Expected demurrage
    # ---------------------------------------------------------
    if (
        expected_delay_hours is not None
        and demurrage_rate_per_day is not None
    ):
        expected_demurrage = (
            expected_delay_hours / 24
        ) * demurrage_rate_per_day

    # ---------------------------------------------------------
    # Total landed cost
    # ---------------------------------------------------------
    if (
        freight_cost is None
        or bunker_cost is None
        or port_cost is None
    ):
        total_landed_cost = None
    else:
        total_landed_cost = (
            freight_cost
            + bunker_cost
            + port_cost
            + (expected_demurrage or 0)
        )

    return {
        "freight_cost": freight_cost,
        "bunker_cost": bunker_cost,
        "port_cost": port_cost,
        "expected_delay_cost": expected_delay_cost,
        "expected_demurrage": expected_demurrage,
        "total_landed_cost": total_landed_cost,
        "currency": "USD",
        "freight_rate_unit": freight_rate_unit,
        "voyage_duration_days": voyage_duration_days,
    }
