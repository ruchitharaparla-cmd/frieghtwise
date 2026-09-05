"""
FreightWise Round 2 — Stage 1: Data Foundation Package
"""

from .status import NOT_AVAILABLE_IN_CURRENT_DATASET, GLOBAL_CONGESTION_PROXY
from .schemas import (
    FreightDatasetSchema,
    FreightModelInputSchema,
    VesselPerformanceSchema,
    IndiaBulkImportsSchema,
    PortCongestionSchema,
)
from .normalization import (
    normalize_dates,
    normalize_country_name,
    normalize_port_name,
    COUNTRY_MAPPING,
    PORT_MAPPING,
)
from .validation import validate_units, validate_schema
from .joins import (
    aggregate_daily_oil_to_monthly,
    aggregate_weekly_congestion_to_monthly,
    safe_join_monthly_freight_with_market,
)
from .quality import generate_data_quality_report
from .features import extract_xgboost_model_features, FEATURE_GROUPS
from .loader import DataLoader

__all__ = [
    "NOT_AVAILABLE_IN_CURRENT_DATASET",
    "GLOBAL_CONGESTION_PROXY",
    "FreightDatasetSchema",
    "FreightModelInputSchema",
    "VesselPerformanceSchema",
    "IndiaBulkImportsSchema",
    "PortCongestionSchema",
    "normalize_dates",
    "normalize_country_name",
    "normalize_port_name",
    "COUNTRY_MAPPING",
    "PORT_MAPPING",
    "validate_units",
    "validate_schema",
    "aggregate_daily_oil_to_monthly",
    "aggregate_weekly_congestion_to_monthly",
    "safe_join_monthly_freight_with_market",
    "generate_data_quality_report",
    "extract_xgboost_model_features",
    "FEATURE_GROUPS",
    "DataLoader",
]
