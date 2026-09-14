from src.decision.contract_optimizer import ContractInput


def build_contract_input_from_forecast(
    current_spot_rate_usd_day: float,
    contract_rate_usd_day: float,
    voyages: int,
    voyage_days: float,
    contract_months: int,
    expected_future_spot_rate_usd_day: float,
    risk_score: float,
) -> ContractInput:
    """
    Build contract-optimizer input using the ML forecast
    as the expected future spot rate.

    Commercial inputs such as current spot rate and
    negotiated contract rate must come from the user/backend.
    """

    return ContractInput(
        current_spot_rate_usd_day=current_spot_rate_usd_day,
        contract_rate_usd_day=contract_rate_usd_day,
        expected_future_spot_rate_usd_day=(
            expected_future_spot_rate_usd_day
        ),
        voyages=voyages,
        voyage_days=voyage_days,
        contract_months=contract_months,
        risk_score=risk_score,
    )