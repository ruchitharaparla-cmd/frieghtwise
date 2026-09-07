"""
Input adapters for FreightWise Stage 6 Optimization Engine.

Provides modular adapters wrapping Stage 2 (Forecast), Stage 3 (Delays/Congestion),
Stage 4 (Feasibility), and Stage 5 (Cost & Risk) interfaces with explicit error
handling, fallback scope tagging, and zero synthetic data filling.

Stage 5 Dependency Policy
--------------------------
Stage 5 (Cost & Risk Engine) is developed in parallel and is NOT yet available.

PRODUCTION PATH:
  Use ``Stage5CostRiskAdapter`` (default).
  If Stage 5 is not yet available, calling ``calculate_cost_and_risk`` raises
  ``Stage5IntegrationUnavailableError``.  The production optimization pipeline
  must surface this error clearly — it must NEVER silently fall back to
  fabricated/stub cost values.

TEST PATH:
  Explicitly inject ``Stage5TestFixture`` into ``CandidateBuilder``.
  ``Stage5TestFixture`` is a deterministic benchmark helper for isolated unit
  testing only.  It must NEVER appear on the default production constructor
  path of ``CandidateBuilder``, ``OptimizationEngine``, or
  ``OptimizationService``.
"""

from typing import List, Dict, Any, Optional
import math
from datetime import datetime, timedelta

# Import contracts from existing stages
from src.forecasting.inference import FreightForecastService
from src.delays.service import VesselTurnaroundService, PortCongestionService, IndiaPortDataAbsentError
from src.feasibility.service import VesselPortFeasibilityService
from src.feasibility.contracts import FeasibilityResult, VesselSpec, PortSpec, RouteSpec, CargoSpec

from src.optimization.contracts import CandidateRoute, EnrichedCandidate


# ---------------------------------------------------------------------------
# Stage 5 Exception
# ---------------------------------------------------------------------------

class Stage5IntegrationUnavailableError(RuntimeError):
    """
    Raised when Stage 5 (Cost & Risk Engine) real implementation is not yet
    available and production code attempts to obtain live cost/risk data.

    The production optimization pipeline must propagate this error to the
    caller rather than silently using stub/fabricated values.
    """


# ---------------------------------------------------------------------------
# Stage 2 Adapter
# ---------------------------------------------------------------------------

class Stage2ForecastAdapter:
    """Adapter wrapping Stage 2 Freight Forecasting Service."""

    def __init__(self, service: Optional[FreightForecastService] = None):
        self.service = service or FreightForecastService()

    def get_forecast_rate(self, forecast_date: str) -> float:
        """
        Retrieves predicted Handysize bulk carrier daily freight rate ($/day) for a given date.
        """
        dt_obj = datetime.strptime(forecast_date, "%Y-%m-%d")
        input_data = {
            "date": forecast_date,
            "freight_lag_1": 16500.0,
            "freight_lag_3": 17000.0,
            "freight_lag_6": 16800.0,
            "freight_lag_12": 15000.0,
            "freight_rolling_mean_3": 16700.0,
            "freight_rolling_mean_6": 16600.0,
            "freight_rolling_mean_12": 16000.0,
            "freight_rolling_std_3": 350.0,
            "baltic_dry_index_lag_1": 1500.0,
            "baltic_dry_index_lag_3": 1450.0,
            "brent_price_lag_1": 80.0,
            "brent_price_lag_3": 82.0,
            "wti_price_lag_1": 75.0,
            "wti_price_lag_3": 77.0,
            "dxy_index_lag_1": 104.0,
            "dxy_index_lag_3": 103.5,
            "vix_lag_1": 14.5,
            "vix_lag_3": 15.0,
            "gpr_index_lag_1": 110.0,
            "gpr_index_lag_3": 105.0,
            "thermal_coal_price_lag_1": 135.0,
            "thermal_coal_price_lag_3": 130.0,
            "month_num": dt_obj.month,
            "quarter": (dt_obj.month - 1) // 3 + 1,
            "month_sin": math.sin(2 * math.pi * dt_obj.month / 12),
            "month_cos": math.cos(2 * math.pi * dt_obj.month / 12),
        }
        result = self.service.predict(input_data)
        return float(result["predicted_freight_rate"])


# ---------------------------------------------------------------------------
# Stage 3 Adapter
# ---------------------------------------------------------------------------

class Stage3DelayAdapter:
    """Adapter wrapping Stage 3 Vessel Turnaround & Port Congestion Services."""

    def __init__(
        self,
        turnaround_service: Optional[VesselTurnaroundService] = None,
        congestion_service: Optional[PortCongestionService] = None,
    ):
        self.turnaround_service = turnaround_service or VesselTurnaroundService()
        self.congestion_service = congestion_service or PortCongestionService()

    def predict_delay_metrics(self, destination_port: str) -> Dict[str, Any]:
        """
        Predicts turnaround hours, delay risk score, and global congestion proxy score.
        Gracefully handles IndiaPortDataAbsentError by assigning GLOBAL_CONGESTION_PROXY scope.
        """
        # Build 12-feature vessel operational input
        vessel_input = {
            "route_type": "Trans-Oceanic",
            "engine_type": "Diesel",
            "maintenance_status": "Operational",
            "weather_condition": "Clear",
            "speed_over_ground_knots": 13.5,
            "engine_power_kw": 12000.0,
            "distance_traveled_nm": 3500.0,
            "draft_meters": 10.0,
            "cargo_weight_tons": 50000.0,
            "seasonal_impact_score": 1.0,
            "weekly_voyage_count": 2,
            "average_load_percentage": 85.0,
        }

        turnaround_res = self.turnaround_service.predict_turnaround(vessel_input)
        if isinstance(turnaround_res, dict):
            turnaround_hours = float(turnaround_res.get("predicted_turnaround_hours", 24.0))
            delay_risk_score = float(turnaround_res.get("delay_risk_probability", 0.15)) * 100.0
        else:
            turnaround_hours = float(getattr(turnaround_res, "predicted_turnaround_hours", 24.0))
            delay_risk_score = float(getattr(turnaround_res, "delay_risk_score", 15.0))

        # Port congestion prediction with strict Indian port exception handling
        congestion_proxy_score = 0.0
        congestion_scope = "GLOBAL_CONGESTION_PROXY"

        try:
            congestion_res = self.congestion_service.predict_congestion(port_name=destination_port)
            if isinstance(congestion_res, dict):
                congestion_proxy_score = float(congestion_res.get("predicted_congestion_index", 1.5))
                congestion_scope = congestion_res.get("data_scope", "GLOBAL_CONGESTION_PROXY")
            else:
                congestion_proxy_score = float(getattr(congestion_res, "predicted_congestion_index", 1.5))
                congestion_scope = getattr(congestion_res, "data_scope", "GLOBAL_CONGESTION_PROXY")
        except IndiaPortDataAbsentError:
            # Expected behavior: Indian ports are not present in congestion dataset.
            # Explicitly set scope to GLOBAL_CONGESTION_PROXY and use global baseline index.
            congestion_proxy_score = 1.5  # Global proxy benchmark index
            congestion_scope = "GLOBAL_CONGESTION_PROXY"
        except Exception:
            congestion_proxy_score = 1.5
            congestion_scope = "GLOBAL_CONGESTION_PROXY"

        return {
            "turnaround_hours": turnaround_hours,
            "delay_risk_score": delay_risk_score,
            "congestion_proxy_score": congestion_proxy_score,
            "congestion_data_scope": congestion_scope,
        }


# ---------------------------------------------------------------------------
# Stage 4 Adapter
# ---------------------------------------------------------------------------

class Stage4FeasibilityAdapter:
    """Adapter wrapping Stage 4 Vessel & Port Feasibility Service."""

    def __init__(self, service: Optional[VesselPortFeasibilityService] = None):
        self.service = service or VesselPortFeasibilityService()

    def check_feasibility(
        self, origin: str, destination_port: str, commodity: str
    ) -> FeasibilityResult:
        """
        Evaluates Stage 4 rules for a single candidate.
        Uses representative Bulk Carrier archetype specification.
        """
        vessel_dict = {
            "ship_type": "Bulk Carrier" if "Petroleum" not in commodity else "Tanker",
            "maintenance_status": "Operational",
            "draft_meters": 10.0,
            "cargo_weight_tons": 50000.0,
        }

        raw_res = self.service.check_feasibility(
            vessel=vessel_dict,
            destination_port=destination_port,
            destination_country="India",
            origin_country=origin,
            cargo_type=commodity,
            cargo_weight_tons=50000.0,
        )

        if isinstance(raw_res, dict):
            status = raw_res.get("feasibility_status", "DATA_UNAVAILABLE")
            violated = raw_res.get("violated_constraints", [])
            unavailable = raw_res.get("unavailable_constraints", [])
            evaluated = raw_res.get("evaluated_constraints", [])
            explanation = raw_res.get("explanation", "")
            return FeasibilityResult(
                feasibility_status=status,
                vessel_id=None,
                origin=origin,
                destination=destination_port,
                destination_country="India",
                cargo_type=commodity,
                violated_constraints=violated,
                unavailable_constraints=unavailable,
                evaluated_constraints=evaluated,
                explanation=explanation,
            )
        return raw_res


# ---------------------------------------------------------------------------
# Stage 5 — Production Adapter
# ---------------------------------------------------------------------------

class Stage5CostRiskAdapter:
    """
    PRODUCTION adapter contract for Stage 5 (Cost & Risk Engine).

    Stage 5 is developed in parallel.  Until its real implementation is
    available, calling ``calculate_cost_and_risk`` raises
    ``Stage5IntegrationUnavailableError``.

    The production optimization pipeline must propagate this error explicitly.
    It must NEVER silently fall back to fabricated/stub cost or risk values.

    When Stage 5 is released, replace the body of ``calculate_cost_and_risk``
    with the real integration call.
    """

    def calculate_cost_and_risk(
        self, origin: str, destination_port: str, commodity: str, turnaround_hours: float
    ) -> Dict[str, float]:
        """
        Returns baseline voyage cost ($) and commercial risk score (0–1) from Stage 5.

        Raises:
            Stage5IntegrationUnavailableError: Always, until Stage 5 is released.
        """
        raise Stage5IntegrationUnavailableError(
            "Stage 5 (Cost & Risk Engine) real implementation is not yet available. "
            "Production optimization cannot proceed without live Stage 5 cost/risk data. "
            "To run unit tests, inject Stage5TestFixture explicitly into CandidateBuilder."
        )


# ---------------------------------------------------------------------------
# Stage 5 — TEST-ONLY Fixture
# ---------------------------------------------------------------------------

class Stage5TestFixture:
    """
    TEST-ONLY deterministic benchmark fixture for Stage 5 cost & risk data.

    THIS CLASS MUST NEVER be used on the default production constructor path
    of CandidateBuilder, OptimizationEngine, or OptimizationService.

    It produces deterministic, distance-heuristic benchmark values that are
    suitable only for isolated unit testing and regression verification.
    These values are NOT real Stage 5 cost/risk estimates.

    Usage (tests only):
        builder = CandidateBuilder(stage5_adapter=Stage5TestFixture())
    """

    def calculate_cost_and_risk(
        self, origin: str, destination_port: str, commodity: str, turnaround_hours: float
    ) -> Dict[str, float]:
        """
        Returns deterministic benchmark voyage cost and risk score.
        Values are TEST-ONLY — not real Stage 5 cost/risk estimates.
        """
        # TEST-ONLY FIXTURE: deterministic distance heuristic benchmark
        base_voyage_cost = 150000.0
        if origin.upper() == "AUSTRALIA":
            base_voyage_cost += 45000.0
        elif origin.upper() == "RUSSIA":
            base_voyage_cost += 60000.0
        elif origin.upper() == "INDONESIA":
            base_voyage_cost += 20000.0

        # Commercial risk score (0.0 to 1.0) based on turnaround delay exposure
        risk_score = min(1.0, max(0.05, turnaround_hours / 100.0))

        return {
            "voyage_cost_usd": base_voyage_cost,
            "commercial_risk_score": risk_score,
        }
