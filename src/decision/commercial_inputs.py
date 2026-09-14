from src.decision.contract_optimizer import ContractInput


def build_contract_input(
    current_spot_rate_usd_day: float,
    contract_rate_usd_day: float,
    voyages: int,
    voyage_days: float,
    contract_months: int,
    expected_future_spot_rate_usd_day: float,
    risk_score: float,
) -> ContractInput:
    """
    Build the validated commercial input object used by
    the FreightWise contract optimizer.

    Commercial values must come from the user/backend.
    The ML system does not fabricate negotiated contract rates.
    """

    return ContractInput(
        current_spot_rate_usd_day=current_spot_rate_usd_day,
        contract_rate_usd_day=contract_rate_usd_day,
        expected_future_spot_rate_usd_day=expected_future_spot_rate_usd_day,
        voyages=voyages,
        voyage_days=voyage_days,
        contract_months=contract_months,
        risk_score=risk_score,
    )