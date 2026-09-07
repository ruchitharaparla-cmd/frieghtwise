"""
Candidate Route Generator & Feasibility Filter for Stage 6 Optimization Engine.

Constructs Cartesian candidate routes across origins, East Coast ports, commodities,
and planning periods. Enforces strict Stage 4 status segregation:
- FEASIBLE -> Admitted to Primary Executable Pool
- INFEASIBLE -> Rejected
- DATA_UNAVAILABLE -> Excluded from default executable plan and reported separately
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.optimization.contracts import (
    CandidateRoute,
    EnrichedCandidate,
    UnavailableCandidateReport,
    CandidateStatusSummary,
    DemandTarget,
    OptimizationRequest,
)
from src.optimization.input_adapter import (
    Stage2ForecastAdapter,
    Stage3DelayAdapter,
    Stage4FeasibilityAdapter,
    Stage5CostRiskAdapter,
    Stage5TestFixture,          # Exposed for explicit test injection only
    Stage5IntegrationUnavailableError,
)

# Supported East Coast Indian Destination Ports
DEFAULT_EAST_COAST_PORTS = [
    "Visakhapatnam SEA",
    "Paradip SEA",
    "Dhamra(Chandbali)",
    "Krishnapatnam",
    "Gangavaram PORT",
    "Kolkata SEA",
    "Gopalpur PORT",
]

# Supported Origin Countries
DEFAULT_ORIGINS = [
    "AUSTRALIA",
    "INDONESIA",
    "RUSSIA",
    "U S A",
    "MOZAMBIQUE",
]


def normalize_commodity_name(commodity: str) -> str:
    """Normalizes input commodity names to match Stage 4 supported commodities."""
    comm_upper = commodity.upper().strip()
    if "COAL" in comm_upper or "COKE" in comm_upper:
        return "Coal"
    elif "IRON" in comm_upper:
        return "Iron Ore"
    elif "FERTILEZER" in comm_upper or "FERTILIZER" in comm_upper:
        if "MANUFACTURED" in comm_upper:
            return "Fertilizers Manufactured"
        return "Fertilizers Crude"
    elif "PETROLEUM" in comm_upper:
        if "PRODUCT" in comm_upper:
            return "Petroleum Products"
        return "Petroleum Crude"
    return commodity


@dataclass
class CandidateBuildResult:
    """Output container for candidate generation & filtering."""
    executable_candidates: List[EnrichedCandidate]
    unavailable_candidates: List[UnavailableCandidateReport]
    infeasible_candidates: List[EnrichedCandidate]
    all_enriched_candidates: List[EnrichedCandidate]
    summary: CandidateStatusSummary


class CandidateBuilder:
    """
    Generates, filters, and enriches candidate routes for optimization.

    Stage 5 Dependency Injection
    -----------------------------
    The ``stage5_adapter`` parameter controls Stage 5 (Cost & Risk) integration.

    PRODUCTION:
        Default ``Stage5CostRiskAdapter()`` raises ``Stage5IntegrationUnavailableError``
        when called.  Do not override this until Stage 5 is released.

    TESTS:
        Explicitly inject ``Stage5TestFixture()`` to use deterministic
        benchmark values.  This fixture must never be used in production.

        Example::

            builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    """

    def __init__(
        self,
        stage2_adapter: Optional[Stage2ForecastAdapter] = None,
        stage3_adapter: Optional[Stage3DelayAdapter] = None,
        stage4_adapter: Optional[Stage4FeasibilityAdapter] = None,
        stage5_adapter=None,
    ):
        self.stage2_adapter = stage2_adapter or Stage2ForecastAdapter()
        self.stage3_adapter = stage3_adapter or Stage3DelayAdapter()
        self.stage4_adapter = stage4_adapter or Stage4FeasibilityAdapter()
        # Default to the production adapter (raises Stage5IntegrationUnavailableError).
        # Tests must explicitly inject Stage5TestFixture.
        self.stage5_adapter = stage5_adapter if stage5_adapter is not None else Stage5CostRiskAdapter()

    def build_and_filter_candidates(
        self,
        request: OptimizationRequest,
        origins: Optional[List[str]] = None,
        ports: Optional[List[str]] = None,
    ) -> CandidateBuildResult:
        """
        Generates Cartesian candidates across (Origins x Ports x Commodities x Periods),
        runs Stage 4 feasibility filtering, enriches with Stage 2/3/5 metrics, and
        segregates into strict executable vs unavailable candidate pools.
        """
        origins = origins or DEFAULT_ORIGINS
        ports = ports or DEFAULT_EAST_COAST_PORTS

        # Determine target commodities from request
        target_commodities = [
            normalize_commodity_name(dt.commodity) for dt in request.demand_targets
        ]
        if not target_commodities:
            target_commodities = ["Coal"]

        # Parse base date for period calculation
        base_date = datetime.strptime(request.planning_start_date, "%Y-%m-%d")

        executable_candidates: List[EnrichedCandidate] = []
        unavailable_candidates: List[UnavailableCandidateReport] = []
        infeasible_candidates: List[EnrichedCandidate] = []
        all_enriched: List[EnrichedCandidate] = []

        total_generated = 0
        feasible_count = 0
        infeasible_count = 0
        data_unavailable_count = 0

        for period in range(1, request.horizon_periods + 1):
            # Calculate period forecast date (monthly increment)
            period_date = (base_date + timedelta(days=30 * (period - 1))).strftime("%Y-%m-%d")
            freight_rate = self.stage2_adapter.get_forecast_rate(period_date)

            for commodity in target_commodities:
                for origin in origins:
                    for port in ports:
                        total_generated += 1

                        cand_route = CandidateRoute(
                            origin=origin,
                            destination_port=port,
                            commodity=commodity,
                            period=period,
                            forecast_date=period_date,
                        )

                        # Stage 4 Feasibility Evaluation
                        feasibility_res = self.stage4_adapter.check_feasibility(
                            origin=origin,
                            destination_port=port,
                            commodity=commodity,
                        )
                        status = feasibility_res.feasibility_status

                        # Stage 3 Operational Metrics
                        delay_metrics = self.stage3_adapter.predict_delay_metrics(port)

                        # Stage 5 Cost & Risk
                        cost_risk = self.stage5_adapter.calculate_cost_and_risk(
                            origin=origin,
                            destination_port=port,
                            commodity=commodity,
                            turnaround_hours=delay_metrics["turnaround_hours"],
                        )

                        archetype_name = (
                            f"Tanker Charter Archetype Slot #{period}"
                            if "Petroleum" in commodity
                            else f"Bulk Carrier Handysize Archetype Slot #{period}"
                        )

                        enriched = EnrichedCandidate(
                            candidate=cand_route,
                            stage4_status=status,
                            stage4_violated_constraints=feasibility_res.violated_constraints,
                            stage4_unavailable_constraints=feasibility_res.unavailable_constraints,
                            forecast_freight_usd_day=freight_rate,
                            turnaround_hours=delay_metrics["turnaround_hours"],
                            delay_risk_score=delay_metrics["delay_risk_score"],
                            congestion_proxy_score=delay_metrics["congestion_proxy_score"],
                            congestion_data_scope=delay_metrics["congestion_data_scope"],
                            voyage_cost_usd=cost_risk["voyage_cost_usd"],
                            commercial_risk_score=cost_risk["commercial_risk_score"],
                            vessel_archetype=archetype_name,
                        )

                        all_enriched.append(enriched)

                        # Strict Segregation Logic per approved plan
                        if status == "FEASIBLE":
                            feasible_count += 1
                            executable_candidates.append(enriched)
                        elif status == "INFEASIBLE":
                            infeasible_count += 1
                            infeasible_candidates.append(enriched)
                        elif status == "DATA_UNAVAILABLE":
                            data_unavailable_count += 1
                            # Exclude from default executable pool; report separately for manual review
                            unavailable_report = UnavailableCandidateReport(
                                candidate_id=cand_route.candidate_id,
                                origin=origin,
                                destination_port=port,
                                commodity=commodity,
                                period=period,
                                stage4_status="DATA_UNAVAILABLE",
                                missing_verification_reasons=feasibility_res.unavailable_constraints
                                or ["Missing verified port channel depth and vessel DWT specifications"],
                            )
                            unavailable_candidates.append(unavailable_report)

        summary = CandidateStatusSummary(
            total_generated=total_generated,
            feasible_count=feasible_count,
            infeasible_count=infeasible_count,
            data_unavailable_count=data_unavailable_count,
        )

        return CandidateBuildResult(
            executable_candidates=executable_candidates,
            unavailable_candidates=unavailable_candidates,
            infeasible_candidates=infeasible_candidates,
            all_enriched_candidates=all_enriched,
            summary=summary,
        )
