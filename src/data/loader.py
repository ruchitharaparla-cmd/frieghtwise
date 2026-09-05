"""
DataLoader module for FreightWise Round 2 — Stage 1.
Provides safe loading, schema validation, date normalization, unit checks, and error handling
for the 10 Stage 1 DataLoader targets.
Operates strictly on DataFrame copies to preserve original Round 1 CSV files.
"""

import os
import pandas as pd
from typing import Optional, Dict

from .schemas import (
    FreightDatasetSchema,
    VesselPerformanceSchema,
    IndiaBulkImportsSchema,
    PortCongestionSchema,
)
from .normalization import normalize_dates, normalize_country_name, normalize_port_name
from .validation import validate_units
from .status import GLOBAL_CONGESTION_PROXY, HISTORICAL_DEMAND_NOT_FORECAST


class DataLoader:
    """
    Unified DataLoader for loading the 10 Stage 1 DataLoader targets:
      1. freight_rates.csv
      2. commodity_prices_processed.csv
      3. oil_geopolitics_processed.csv
      4. port_congestion_processed.csv
      5. trade_flows_processed.csv
      6. vessel_performance_processed.csv
      7. india_bulk_imports_2022_2026.csv
      8. monthly_freight_ml.csv
      9. freight_model_features.csv
     10. route_demand_summary.csv
    """

    DEFAULT_DATA_DIR = "data/processed"

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or self.DEFAULT_DATA_DIR

    def _get_path(self, filename: str) -> str:
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required Stage 1 processed dataset not found at path: {path}")
        return path

    def load_freight_rates(self) -> pd.DataFrame:
        """Loads 1. freight_rates.csv (300 rows, 2000-2024 monthly)."""
        path = self._get_path("freight_rates.csv")
        df = pd.read_csv(path)
        df_norm = normalize_dates(df, date_col="date")
        validate_units(df_norm, "freight_rates")
        return df_norm

    def load_commodity_prices(self) -> pd.DataFrame:
        """Loads 2. commodity_prices_processed.csv (1176 rows, 2010-2026 monthly)."""
        path = self._get_path("commodity_prices_processed.csv")
        df = pd.read_csv(path)
        df_norm = normalize_dates(df, date_col="date")
        return df_norm

    def load_oil_geopolitics(self) -> pd.DataFrame:
        """Loads 3. oil_geopolitics_processed.csv (4047 rows, 2010-2026 daily)."""
        path = self._get_path("oil_geopolitics_processed.csv")
        df = pd.read_csv(path)
        df_norm = normalize_dates(df, date_col="date")
        return df_norm

    def load_port_congestion(self) -> pd.DataFrame:
        """
        Loads 4. port_congestion_processed.csv (6260 rows, 2019-2024 weekly).
        Tagged as GLOBAL_CONGESTION_PROXY (0 Indian ports).
        """
        path = self._get_path("port_congestion_processed.csv")
        df = pd.read_csv(path)
        PortCongestionSchema.validate(df)
        df_norm = normalize_dates(df, date_col="week_start")
        df_norm.attrs["proxy_tag"] = GLOBAL_CONGESTION_PROXY
        return df_norm

    def load_trade_flows(self) -> pd.DataFrame:
        """Loads 5. trade_flows_processed.csv (1250 rows, 2000-2024 annual)."""
        path = self._get_path("trade_flows_processed.csv")
        df = pd.read_csv(path)
        df_norm = normalize_dates(df, date_col="year")
        return df_norm

    def load_vessel_performance(self, filter_bulk_carrier: bool = False) -> pd.DataFrame:
        """
        Loads 6. vessel_performance_processed.csv (2736 rows, 2023-2024 voyage/daily).
        Optionally filters for ship_type == 'Bulk Carrier' (669 rows).
        """
        path = self._get_path("vessel_performance_processed.csv")
        df = pd.read_csv(path)
        VesselPerformanceSchema.validate(df)
        df_norm = normalize_dates(df, date_col="date")
        validate_units(df_norm, "vessel_performance")

        if filter_bulk_carrier:
            df_norm = df_norm[df_norm["ship_type"] == "Bulk Carrier"].copy()

        return df_norm

    def load_india_bulk_imports(self, normalize_entities: bool = True) -> pd.DataFrame:
        """
        Loads 7. india_bulk_imports_2022_2026.csv (11200 rows, 2022-2026 monthly/periodic).
        Validates 100% TON unit. Optionally normalizes country/port text variants on copies.
        """
        path = self._get_path("india_bulk_imports_2022_2026.csv")
        df = pd.read_csv(path)
        IndiaBulkImportsSchema.validate(df)
        df_norm = normalize_dates(df, date_col="Period_Start")
        validate_units(df_norm, "india_bulk_imports")

        if normalize_entities:
            df_norm["Country_Normalized"] = df_norm["Country_of_Consignment"].apply(normalize_country_name)
            df_norm["Port_Normalized"] = df_norm["Port"].apply(normalize_port_name)

        return df_norm

    def load_monthly_freight_ml(self) -> pd.DataFrame:
        """Loads 8. monthly_freight_ml.csv (179 rows, 2010-2024 monthly)."""
        path = self._get_path("monthly_freight_ml.csv")
        df = pd.read_csv(path)
        df_norm = normalize_dates(df, date_col="date")
        return df_norm

    def load_freight_model_features(self) -> pd.DataFrame:
        """
        Loads 9. freight_model_features.csv (167 rows, 46 columns, 2011-2024 monthly).
        Validates the 46-column dataset schema contract.
        """
        path = self._get_path("freight_model_features.csv")
        df = pd.read_csv(path)
        FreightDatasetSchema.validate(df)
        df_norm = normalize_dates(df, date_col="date")
        return df_norm

    def load_route_demand_summary(self) -> pd.DataFrame:
        """
        Loads 10. route_demand_summary.csv (40 rows).
        Explicitly tagged as HISTORICAL_DEMAND_NOT_FORECAST.
        """
        path = self._get_path("route_demand_summary.csv")
        df = pd.read_csv(path)
        df.attrs["tag"] = HISTORICAL_DEMAND_NOT_FORECAST
        return df.copy()

    def load_all_targets(self) -> Dict[str, pd.DataFrame]:
        """
        Loads all 10 Stage 1 DataLoader targets in a single call.
        Returns a dictionary mapping target names to DataFrames.
        """
        return {
            "freight_rates": self.load_freight_rates(),
            "commodity_prices": self.load_commodity_prices(),
            "oil_geopolitics": self.load_oil_geopolitics(),
            "port_congestion": self.load_port_congestion(),
            "trade_flows": self.load_trade_flows(),
            "vessel_performance": self.load_vessel_performance(),
            "india_bulk_imports": self.load_india_bulk_imports(),
            "monthly_freight_ml": self.load_monthly_freight_ml(),
            "freight_model_features": self.load_freight_model_features(),
            "route_demand_summary": self.load_route_demand_summary(),
        }
