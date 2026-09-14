from dataclasses import dataclass
from typing import Optional


@dataclass
class ContractInput:
    current_spot_rate_usd_day: float
    contract_rate_usd_day: float
    expected_future_spot_rate_usd_day: float
    voyages: int
    voyage_days: float
    contract_months: int
    risk_score: float


def validate_input(data: ContractInput):
    if data.current_spot_rate_usd_day <= 0:
        raise ValueError("Current spot rate must be positive.")

    if data.contract_rate_usd_day <= 0:
        raise ValueError("Contract rate must be positive.")

    if data.expected_future_spot_rate_usd_day <= 0:
        raise ValueError(
            "Expected future spot rate must be positive."
        )

    if data.voyages <= 0:
        raise ValueError("Number of voyages must be positive.")

    if data.voyage_days <= 0:
        raise ValueError("Voyage duration must be positive.")

    if data.contract_months <= 0:
        raise ValueError(
            "Contract duration must be positive."
        )

    if not 0 <= data.risk_score <= 100:
        raise ValueError(
            "Risk score must be between 0 and 100."
        )


def calculate_costs(data: ContractInput):
    validate_input(data)

    total_voyage_days = data.voyages * data.voyage_days

    spot_cost = (
        data.current_spot_rate_usd_day
        * total_voyage_days
    )

    future_spot_cost = (
        data.expected_future_spot_rate_usd_day
        * total_voyage_days
    )

    contract_cost = (
        data.contract_rate_usd_day
        * total_voyage_days
    )

    savings_vs_current_spot = (
        spot_cost - contract_cost
    )

    savings_vs_future_spot = (
        future_spot_cost - contract_cost
    )

    savings_percentage = (
        savings_vs_current_spot
        / spot_cost
        * 100
    )

    # Risk premium increases the effective cost
    # of relying on future spot-market exposure.
    risk_premium = (
        future_spot_cost
        * (data.risk_score / 100)
        * 0.20
    )

    risk_adjusted_future_spot_cost = (
        future_spot_cost + risk_premium
    )

    return {
        "spot_cost": spot_cost,
        "future_spot_cost": future_spot_cost,
        "contract_cost": contract_cost,
        "savings_vs_current_spot": savings_vs_current_spot,
        "savings_vs_future_spot": savings_vs_future_spot,
        "savings_percentage": savings_percentage,
        "risk_premium": risk_premium,
        "risk_adjusted_future_spot_cost":
            risk_adjusted_future_spot_cost,
    }


def recommend_strategy(data: ContractInput, costs):
    current_spot = data.current_spot_rate_usd_day
    contract = data.contract_rate_usd_day
    future_spot = data.expected_future_spot_rate_usd_day
    risk = data.risk_score

    # Contract is cheaper than both current and
    # expected future spot exposure.
    if (
        contract < current_spot
        and contract < future_spot
        and costs["savings_percentage"] >= 5
        and risk < 66
    ):
        if data.contract_months >= 6:
            return (
                "CHARTER NOW",
                "MEDIUM-TERM MULTI-VOYAGE CONTRACT",
            )

        return (
            "CHARTER NOW",
            "SHORT-TERM MULTI-VOYAGE CONTRACT",
        )

    # High risk makes a long commitment less attractive.
    if risk >= 66:
        return (
            "CAUTIOUS / REVIEW",
            "FLEXIBLE OR SHORTER CONTRACT",
        )

    # If future spot rates are expected to decline,
    # waiting may be better than locking in.
    if future_spot < current_spot * 0.95:
        return (
            "WAIT",
            "DEFER CONTRACT AND MONITOR MARKET",
        )

    # Contract provides some savings but not enough
    # for a strong commitment.
    if contract < current_spot:
        return (
            "PARTIAL",
            "PARTIAL MULTI-VOYAGE CONTRACT",
        )

    return (
        "WAIT",
        "COMPARE SPOT VOYAGES",
    )


def optimize_contract(data: ContractInput):
    costs = calculate_costs(data)

    recommendation, contract_strategy = (
        recommend_strategy(data, costs)
    )

    result = {
        "recommendation": recommendation,
        "contract_strategy": contract_strategy,
        "contract_months": data.contract_months,
        "voyages": data.voyages,
        "voyage_days": data.voyage_days,
        "current_spot_rate_usd_day":
            data.current_spot_rate_usd_day,
        "expected_future_spot_rate_usd_day":
            data.expected_future_spot_rate_usd_day,
        "contract_rate_usd_day":
            data.contract_rate_usd_day,
        "risk_score": data.risk_score,
        **costs,
    }

    return result


def main():
    print("Contract Optimizer module loaded successfully.")
    print(
        "Use optimize_contract() with verified "
        "commercial inputs."
    )


if __name__ == "__main__":
    main()