"""
Date and entity normalization utilities for FreightWise Stage 1 Data Foundation.
All functions operate strictly on DataFrame copies to ensure immutability of source data.
"""

import pandas as pd
from typing import Dict, Optional


COUNTRY_MAPPING: Dict[str, str] = {
    "U S A": "USA",
    "U ARAB EMTS": "UAE",
    "U K": "UK",
    "SOUTH AFRICA": "South Africa",
    "CHINA P RP": "China",
    "GERMANY": "Germany",
    "RUSSIA": "Russia",
    "INDONESIA": "Indonesia",
    "SINGAPORE": "Singapore",
    "AUSTRALIA": "Australia",
    "OMAN": "Oman",
    "SAUDI ARAB": "Saudi Arabia",
    "NETHERLAND": "Netherlands",
    "SPAIN": "Spain",
    "JAPAN": "Japan",
}

PORT_MAPPING: Dict[str, str] = {
    "VISAKHAPATNAM SEA": "Visakhapatnam Port",
    "PARADIP SEA": "Paradip Port",
    "NHAVA SHEVA SEA": "Nhava Sheva Port",
    "CHENNAI SEA": "Chennai Port",
    "KOLKATA SEA": "Kolkata Port",
    "MUNDRA": "Mundra Port",
    "KANDLA SEA": "Kandla Port",
    "KAKINADA SEA": "Kakinada Port",
    "KRISHNAPATNAM": "Krishnapatnam Port",
    "TUTICORIN SEA": "Tuticorin Port",
    "COCHIN SEA": "Cochin Port",
}


def normalize_country_name(name: str) -> str:
    """Normalize textual variant of country name."""
    if not isinstance(name, str):
        return name
    name_clean = name.strip()
    return COUNTRY_MAPPING.get(name_clean, name_clean)


def normalize_port_name(name: str) -> str:
    """Normalize textual variant of Indian port name."""
    if not isinstance(name, str):
        return name
    name_clean = name.strip()
    return PORT_MAPPING.get(name_clean, name_clean)


def normalize_dates(df: pd.DataFrame, date_col: Optional[str] = None) -> pd.DataFrame:
    """
    Normalizes date fields in a DataFrame copy.
    Derives canonical year_month (YYYY-MM) and monthly start date (YYYY-MM-01) where appropriate.
    Does NOT modify the original DataFrame object.
    """
    df_copy = df.copy()

    # Auto-detect date column if not specified
    if date_col is None:
        possible_cols = ["date", "Date", "week_start", "Period_Start", "year"]
        for c in possible_cols:
            if c in df_copy.columns:
                date_col = c
                break

    if date_col is None or date_col not in df_copy.columns:
        return df_copy

    if date_col == "year":
        # Integer year column (e.g. trade flows)
        df_copy["year"] = df_copy["year"].astype(int)
        if "year_month" not in df_copy.columns:
            df_copy["year_month"] = df_copy["year"].astype(str) + "-01"
        return df_copy

    # Parse datetime
    dt_series = pd.to_datetime(df_copy[date_col], errors="coerce")

    # Standardize string date format YYYY-MM-DD
    if date_col in ["date", "Date", "week_start", "Period_Start"]:
        df_copy[date_col] = dt_series.dt.strftime("%Y-%m-%d")

    # Derive year_month YYYY-MM
    if "year_month" not in df_copy.columns:
        df_copy["year_month"] = dt_series.dt.strftime("%Y-%m")

    # Derive canonical_month_start YYYY-MM-01 for monthly alignment
    if "canonical_month_start" not in df_copy.columns:
        df_copy["canonical_month_start"] = dt_series.dt.strftime("%Y-%m-01")

    return df_copy
