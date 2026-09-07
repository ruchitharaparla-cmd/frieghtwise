"""Deterministic Stage 5 cost and risk calculations."""

from typing import Any, Dict, Mapping, Optional

from .contracts import COST_STATUSES, RISK_STATUSES, CostRiskEvaluation, ProjectParameters


class Stage5CalculationEngine:
    """Calculate component values for Stage 6 without making decisions."""

    def __init__(
        self,
        project_parameters: Optional[ProjectParameters] = None,
        delay_service: Optional[Any] = None,
        congestion_service: Optional[Any] = None,
        feasibility_service: Optional[Any] = None,
    ) -> None:
        self.parameters = project_parameters or ProjectParameters()
        self.delay_service = delay_service
        self.congestion_service = congestion_service
        self.feasibility_service = feasibility_service

    @staticmethod
    def _component(
        name: str,
        value: Optional[float],
        unit: str,
        status: str,
        assumptions: list[str],
        data_scope: str,
        source: Mapping[str, Any],
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        if status not in COST_STATUSES and status not in RISK_STATUSES and not status.startswith("UNAVAILABLE_"):
            raise ValueError(f"Unsupported Stage 5 component status: {status}")
        return {
            "name": name,
            "value": value,
            "unit": unit,
            "currency": currency,
            "status": status,
            "assumptions": list(assumptions),
            "data_scope": data_scope,
            "source": dict(source),
        }

    def _cost_component(
        self,
        name: str,
        value: Optional[float],
        unit: str,
        source: Mapping[str, Any],
        assumptions: list[str],
        data_scope: str,
        status: str = "KNOWN",
    ) -> Dict[str, Any]:
        if value is None and not status.startswith("UNAVAILABLE"):
            status = "UNAVAILABLE"
        return self._component(name, value, unit, status, assumptions, data_scope, source, self.parameters.default_currency)

    def _unavailable_cost(self, name: str, reason: str, unit: str) -> Dict[str, Any]:
        return self._cost_component(
            name, None, unit, {"type": "input", "field": name},
            [f"No verified {name} input was supplied."], "CURRENT_INPUTS", f"UNAVAILABLE_{reason}",
        )

    def _invoke_stage3(
        self,
        service: Any,
        method_name: str,
        payload: Optional[Mapping[str, Any]],
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        if service is None or payload is None:
            return None, "INPUT_NOT_PROVIDED"
        try:
            return dict(getattr(service, method_name)(payload)), None
        except Exception as exc:
            return None, type(exc).__name__

    def _risk_component(
        self,
        name: str,
        value: Optional[float],
        unit: str,
        status: str,
        assumptions: list[str],
        data_scope: str,
        source: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if status not in RISK_STATUSES and not status.startswith("UNAVAILABLE_"):
            raise ValueError(f"Unsupported Stage 5 risk status: {status}")
        return self._component(name, value, unit, status, assumptions, data_scope, source)

    def calculate(
        self,
        *,
        quantity_tonnes: Optional[float] = None,
        freight_rate: Optional[float] = None,
        bunker_cost: Optional[float] = None,
        port_charges: Optional[float] = None,
        demurrage_rate_per_day: Optional[float] = None,
        insurance_cost: Optional[float] = None,
        congestion_surcharge: Optional[float] = None,
        delay_cost: Optional[float] = None,
        expected_delay_hours: Optional[float] = None,
        delay_input: Optional[Mapping[str, Any]] = None,
        congestion_input: Optional[Mapping[str, Any]] = None,
        weather_context: Optional[Mapping[str, Any]] = None,
        verified_future_weather: bool = False,
        feasibility_input: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        assumptions = [
            "Stage 5 performs deterministic component calculations only.",
            "Unavailable numerical inputs remain None and are never treated as zero.",
            "Project parameters are configuration values, not universal maritime constants.",
        ]
        delay_result, delay_error = self._invoke_stage3(self.delay_service, "predict_turnaround", delay_input)
        calculated_delay_hours = expected_delay_hours
        if calculated_delay_hours is None and delay_result is not None:
            calculated_delay_hours = delay_result.get("predicted_turnaround_hours")
        components: Dict[str, Dict[str, Any]] = {}
        if quantity_tonnes is not None and freight_rate is not None:
            components["freight"] = self._cost_component(
                "freight", quantity_tonnes * freight_rate, "total",
                {"type": "input", "fields": ["quantity_tonnes", "freight_rate"]},
                ["Freight equals quantity_tonnes multiplied by freight_rate."], "CURRENT_INPUTS",
            )
        else:
            components["freight"] = self._unavailable_cost("freight", "MISSING_INPUT", "total")
        components["bunker"] = self._cost_component(
            "bunker", bunker_cost, "total", {"type": "input", "field": "bunker_cost"}, [], "CURRENT_INPUTS",
        ) if bunker_cost is not None else self._unavailable_cost("bunker", "MISSING_INPUT", "total")
        components["port_charges"] = self._cost_component(
            "port_charges", port_charges, "total", {"type": "input", "field": "port_charges"}, [], "CURRENT_INPUTS",
        ) if port_charges is not None else self._unavailable_cost("port_charges", "MISSING_INPUT", "total")
        if calculated_delay_hours is not None and demurrage_rate_per_day is not None:
            demurrage = calculated_delay_hours / self.parameters.hours_per_day * demurrage_rate_per_day
            components["demurrage"] = self._cost_component(
                "demurrage", demurrage, "total",
                {"type": "stage3_or_input", "fields": ["expected_delay_hours", "demurrage_rate_per_day"]},
                ["Demurrage uses the configurable project hours_per_day parameter."], "CURRENT_INPUTS",
            )
        else:
            components["demurrage"] = self._unavailable_cost("demurrage", "MISSING_INPUT", "total")
        for name, value in (("insurance", insurance_cost), ("congestion_surcharge", congestion_surcharge), ("delay_cost", delay_cost)):
            components[name] = self._cost_component(
                name, value, "total", {"type": "input", "field": name}, [], "CURRENT_INPUTS",
            ) if value is not None else self._unavailable_cost(name, "MISSING_INPUT", "total")

        missing = [name for name in self.parameters.required_cost_components if components[name]["value"] is None]
        total_known_cost = sum(
            component["value"] for component in components.values()
            if component["value"] is not None and component["status"] == "KNOWN"
        )
        cost_completeness = "COMPLETE" if not missing else "PARTIAL"

        delay_value = calculated_delay_hours
        delay_source: Dict[str, Any] = {"type": "input", "field": "expected_delay_hours"}
        delay_scope = "CURRENT_INPUTS"
        if delay_result is not None:
            delay_value = delay_result.get("predicted_turnaround_hours")
            delay_source = delay_result
            delay_scope = "STAGE3_VESSEL_TURNAROUND"
        risk: Dict[str, Dict[str, Any]] = {
            "delay": self._risk_component(
                "delay", delay_value, "hours", "KNOWN" if delay_value is not None else "UNAVAILABLE_INPUT_NOT_PROVIDED",
                [], delay_scope, delay_source,
            )
        }
        congestion_result, congestion_error = self._invoke_stage3(self.congestion_service, "predict_congestion", congestion_input)
        if congestion_result is not None:
            risk["congestion"] = self._risk_component(
                "congestion", congestion_result.get("risk_probability"), "probability", "KNOWN",
                ["Congestion retains the scope declared by Stage 3."], congestion_result.get("data_scope", "GLOBAL_CONGESTION_PROXY"), congestion_result,
            )
        else:
            risk["congestion"] = self._risk_component(
                "congestion", None, "probability", f"UNAVAILABLE_{congestion_error or 'NOT_PROVIDED'}", [],
                "GLOBAL_CONGESTION_PROXY" if congestion_input else "CURRENT_INPUTS", {"type": "stage3", "error": congestion_error},
            )
        if weather_context is not None and not verified_future_weather:
            risk["weather"] = self._risk_component(
                "weather", weather_context.get("risk_value"), "contextual", "HISTORICAL_CONTEXT_ONLY",
                ["Historical weather is contextual only and is not a future numerical forecast."], "HISTORICAL", weather_context,
            )
        elif verified_future_weather:
            risk["weather"] = self._risk_component(
                "weather", weather_context.get("risk_value") if weather_context else None, "score",
                "KNOWN" if weather_context and weather_context.get("risk_value") is not None else "UNAVAILABLE_MISSING_INPUT",
                [], "VERIFIED_FUTURE_FORECAST", weather_context or {},
            )
        else:
            risk["weather"] = self._risk_component("weather", None, "score", "UNAVAILABLE_NOT_PROVIDED", [], "CURRENT_INPUTS", {"type": "input"})
        risk_status = "COMPLETE" if all(item["value"] is not None for item in risk.values()) else "PARTIAL"
        feasibility = self._evaluate_feasibility(feasibility_input)
        return CostRiskEvaluation(
            cost_components=components,
            total_known_cost=total_known_cost,
            cost_completeness=cost_completeness,
            missing_cost_components=missing,
            risk_components=risk,
            risk_status=risk_status,
            risk_completeness=risk_status,
            feasibility=feasibility,
            calculation_assumptions=assumptions,
            project_parameters=self.parameters.to_dict(),
            provenance={
                "stage": "5",
                "engine": "deterministic",
                "stage3_delay_error": delay_error,
                "stage3_congestion_error": congestion_error,
            },
        ).to_dict()

    def _evaluate_feasibility(self, payload: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
        if self.feasibility_service is None or payload is None:
            return {"status": "DATA_UNAVAILABLE", "source": "stage4", "evaluated": False}
        try:
            evaluator = getattr(self.feasibility_service, "check_feasibility", self.feasibility_service)
            result = evaluator(**dict(payload))
            result = result.to_dict() if hasattr(result, "to_dict") else dict(result)
            return {"status": result.get("feasibility_status", "DATA_UNAVAILABLE"), "source": "stage4", "result": result, "evaluated": True}
        except Exception as exc:
            return {"status": "DATA_UNAVAILABLE", "source": "stage4", "error": type(exc).__name__, "evaluated": False}