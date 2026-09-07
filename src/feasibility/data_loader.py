"""
Data loader for FreightWise Stage 4 Feasibility Engine.

Loads verified constraint data from Stage 1 processed datasets.
Implements strict data honesty: no synthetic data generation.
"""

import os
from typing import Dict, List, Any, Optional
import pandas as pd

from src.feasibility.contracts import (
    COMMODITY_TO_VESSEL_TYPES,
    INDIAN_SEA_PORTS,
)
from src.feasibility.exceptions import DataUnavailableError


class ConstraintDataLoader:
    """
    Loads and caches verified constraint data from Stage 1 sources.

    All data is loaded from actual processed CSV files; no synthetic data is generated.
    Missing data raises explicit DataUnavailableError rather than inventing values.
    """

    DATA_DIR = "data/processed"

    def __init__(self):
        self.route_demand_df: Optional[pd.DataFrame] = None
        self.commodity_mapping: Dict[str, List[str]] = COMMODITY_TO_VESSEL_TYPES
        self._loaded = False

    def load_all(self) -> None:
        """Pre-load all constraint data into memory."""
        if self._loaded:
            return

        try:
            self.route_demand_df = self._load_route_demand()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Required Stage 1 data file not found: {e}. "
                "Ensure data/processed/route_demand_summary.csv exists."
            )

        self._loaded = True

    def _load_route_demand(self) -> pd.DataFrame:
        """Load route demand summary from Stage 1 data."""
        path = os.path.join(self.DATA_DIR, "route_demand_summary.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Route demand data not found at {path}")

        df = pd.read_csv(path)

        # Validate expected columns
        expected_cols = ["Country_of_Consignment", "Port", "demand_score", "route_priority"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            raise ValueError(
                f"Route demand CSV missing expected columns: {missing}. "
                f"Found columns: {list(df.columns)}"
            )

        return df

    def check_route_exists(self, origin_country: str, destination_port: str) -> Dict[str, Any]:
        """
        Checks if origin-destination route exists in historical data.

        Returns:
            Dict with keys:
            - exists: bool
            - demand_score: float (0-1) if exists
            - route_priority: str (High/Medium/Low) if exists
            - quantity_tons: int if exists

        Raises:
            DataUnavailableError if route demand data not loaded
        """
        if self.route_demand_df is None:
            self.load_all()

        # Case-insensitive search
        origin_lower = origin_country.lower()
        port_lower = destination_port.lower()

        matching_rows = self.route_demand_df[
            (self.route_demand_df["Country_of_Consignment"].str.lower() == origin_lower) &
            (self.route_demand_df["Port"].str.lower() == port_lower)
        ]

        if len(matching_rows) > 0:
            row = matching_rows.iloc[0]
            return {
                "exists": True,
                "demand_score": float(row.get("demand_score", 0.0)),
                "route_priority": str(row.get("route_priority", "Low")),
                "quantity_tons": int(row.get("total_quantity", 0)),
            }
        else:
            return {
                "exists": False,
                "demand_score": None,
                "route_priority": None,
                "quantity_tons": None,
            }

    def get_commodity_vessel_types(self, commodity: str) -> Optional[List[str]]:
        """
        Get compatible vessel types for a commodity.

        Returns None if commodity not in supported list.
        """
        return self.commodity_mapping.get(commodity)

    def is_indian_port(self, port_name: str, country: str) -> bool:
        """Checks if port is an identified Indian port (no verified infrastructure specs)."""
        if country.lower() == "india":
            return True
        if any(indicator in port_name for indicator in INDIAN_SEA_PORTS):
            return True
        return False

    def get_port_draft_limit(self, port_name: str, country: str) -> Optional[float]:
        """
        Get verified maximum draft limit for a port.

        Returns:
            float: Maximum channel depth in meters, if verified
            None: If not available (especially for Indian ports)

        CRITICAL: Never invents Indian port depths.
        """
        if self.is_indian_port(port_name, country):
            # Explicitly unavailable for Indian ports
            return None

        # For other ports: check if data exists (currently no global specs in dataset)
        # Future: integrate external port master data
        return None

    def get_vessel_capacity_dwt(self, ship_type: str) -> Optional[float]:
        """
        Get typical vessel capacity (DWT) for a ship type.

        Returns:
            float: Typical DWT in tons, if verified
            None: If not available

        NOTE: Current dataset does not include vessel DWT specifications.
        This placeholder supports future data enrichment.
        """
        # Current vessel_performance_processed.csv does not include DWT
        # Only cargo_weight_tons from historical voyages is available
        return None

    def get_vessel_dimensions(self, ship_type: str) -> Optional[Dict[str, float]]:
        """
        Get typical vessel dimensions (LOA, beam) for a ship type.

        Returns:
            Dict with 'loa_meters' and 'beam_meters', if verified
            None: If not available

        NOTE: Current dataset does not include vessel dimension specifications.
        """
        # Current vessel_performance_processed.csv does not include LOA/beam
        return None
