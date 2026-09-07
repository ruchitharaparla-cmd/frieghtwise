from typing import Optional


def calculate_cost(
    quantity_tonnes: float,
    freight_rate: Optional[float],
    bunker_cost: Optional[float],
    port_cost: Optional[float],
    expected_delay_hours: Optional[float],
    demurrage_rate_per_day: Optional[float],
):
    freight_cost = None
    expected_delay_cost = None
    expected_demurrage = None

    # Freight cost
    if freight_rate is not None:
        freight_cost = quantity_tonnes * freight_rate

    # Demurrage is calculated only when both delay
    # and demurrage rate are available.
    if (
        expected_delay_hours is not None
        and demurrage_rate_per_day is not None
    ):
        expected_demurrage = (
            expected_delay_hours / 24
        ) * demurrage_rate_per_day

    # Total landed cost
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
    }