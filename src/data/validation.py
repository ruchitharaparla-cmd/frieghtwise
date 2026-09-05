"""
Unit validation and schema enforcement utilities for FreightWise Stage 1 Data Foundation.
"""

import pandas as pd
from typing import Dict, Any, List


CANONICAL_UNITS: Dict[str, str] = {
    "freight": "USD/day",
    "tanker_rate": "USD/day",
    "container_rate": "USD/FEU",
    "air_cargo_rate": "USD/kg",
    "india_import_quantity": "TON",
    "vessel_cargo": "Metric Tons",
    "distance": "nautical miles",
    "speed": "knots",
    "draft": "meters",
    "engine_power": "kW",
    "turnaround": "hours",
    "wait_days": "days",
    "berth_delay": "hours",
    "operational_cost": "USD",
    "revenue": "USD",
}


def validate_units(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """
    Validates documented units for a given dataset without silent mutation.
    Returns unit validation report dictionary.
    """
    report = {"dataset": dataset_name, "valid": True, "details": []}

    if dataset_name == "india_bulk_imports":
        if "Unit" in df.columns:
            units_present = df["Unit"].unique().tolist()
            if units_present == ["TON"]:
                report["details"].append("India bulk imports unit verified: 100% Metric Tons (TON)")
            else:
                report["valid"] = False
                report["details"].append(f"Unexpected units found in India bulk imports: {units_present}")

    elif dataset_name == "vessel_performance":
        required_numeric = [
            "speed_over_ground_knots",
            "engine_power_kw",
            "distance_traveled_nm",
            "draft_meters",
            "cargo_weight_tons",
            "operational_cost_usd",
            "revenue_per_voyage_usd",
            "turnaround_time_hours",
        ]
        missing = [c for c in required_numeric if c not in df.columns]
        if missing:
            report["valid"] = False
            report["details"].append(f"Missing expected unit columns in vessel performance: {missing}")
        else:
            report["details"].append("Vessel performance units verified: knots, kW, nm, meters, tons, USD, hours")

    elif dataset_name == "freight_rates":
        if "bulk_carrier_handysize_usd_day" in df.columns:
            report["details"].append("Freight rate unit verified: USD/day")
        else:
            report["valid"] = False
            report["details"].append("Missing bulk_carrier_handysize_usd_day column")

    return report


def validate_schema(df: pd.DataFrame, schema_cls: Any) -> bool:
    """
    Enforces a schema contract class against a DataFrame.
    Raises ValueError if contract is violated.
    """
    return schema_cls.validate(df)
