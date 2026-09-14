from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/processed")
OUTPUT_FILE = DATA_DIR / "risk_idle_analysis.csv"


EAST_COAST_PORT_KEYWORDS = [
    "CHENNAI",
    "KATTUPALLI",
    "ENNORE",
    "KAMARAJAR",
    "KRISHNAPATNAM",
    "KAKINADA",
    "VISAKHAPATNAM",
    "VISAKH",
    "GANGAVARAM",
    "GOPALPUR",
    "DHAMRA",
    "PARADIP",
    "KOLKATA",
    "HALDIA",
    "TUTICORIN",
    "CHIDAMBARANAR",
]


def minmax_score(
    series: pd.Series,
    higher_is_riskier: bool = True,
) -> pd.Series:
    """Convert a numeric series to a 0-100 risk score."""

    s = pd.to_numeric(series, errors="coerce")

    if s.notna().sum() == 0:
        return pd.Series(np.nan, index=series.index)

    minimum = s.min()
    maximum = s.max()

    if maximum == minimum:
        score = pd.Series(50.0, index=series.index)
    else:
        score = (
            (s - minimum)
            / (maximum - minimum)
            * 100
        )

    if not higher_is_riskier:
        score = 100 - score

    return score


def risk_level(score):
    """Convert a 0-100 score into LOW/MEDIUM/HIGH."""

    if pd.isna(score):
        return "UNKNOWN"

    if score < 33:
        return "LOW"

    if score < 66:
        return "MEDIUM"

    return "HIGH"


def is_east_coast_port(port_name):
    """Check whether a port is a relevant Indian East Coast port."""

    if pd.isna(port_name):
        return False

    port = str(port_name).upper().strip()

    return any(
        keyword in port
        for keyword in EAST_COAST_PORT_KEYWORDS
    )


def is_ocean_port(port_name):
    """
    Keep East Coast seaports while excluding obvious
    airports, ICDs, CFSs and SEZs.
    """

    if pd.isna(port_name):
        return False

    port = str(port_name).upper().strip()

    excluded_keywords = [
        " AIR",
        "AIR ",
        "AIRPORT",
        "ICD",
        "CFS",
        "SEZ",
        "INLAND",
        "DRY PORT",
        "LAND CUSTOM",
    ]

    if any(
        keyword in port
        for keyword in excluded_keywords
    ):
        return False

    return is_east_coast_port(port_name)


def load_data():
    """Load all datasets required for Risk + Idle Management."""

    freight = pd.read_csv(
        DATA_DIR / "freight_forecast_predictions.csv"
    )

    market = pd.read_csv(
        DATA_DIR / "oil_geopolitics_processed.csv"
    )

    congestion = pd.read_csv(
        DATA_DIR / "port_congestion_processed.csv"
    )

    demand = pd.read_csv(
        DATA_DIR / "route_demand_summary.csv"
    )

    vessel = pd.read_csv(
        DATA_DIR / "vessel_performance_processed.csv"
    )

    india_imports = pd.read_csv(
        DATA_DIR / "india_bulk_imports_2022_2026.csv"
    )

    return (
        freight,
        market,
        congestion,
        demand,
        vessel,
        india_imports,
    )


def prepare_market_risk(market):
    """Calculate monthly market risk."""

    market = market.copy()

    market["date"] = pd.to_datetime(
        market["date"],
        errors="coerce",
    )

    market = market.dropna(subset=["date"])

    monthly = (
        market.groupby(
            market["date"].dt.to_period("M")
        )
        .agg(
            vix=("vix", "mean"),
            gpr_index=("gpr_index", "mean"),
            brent_volatility_30d=(
                "brent_volatility_30d",
                "mean",
            ),
            wti_volatility_30d=(
                "wti_volatility_30d",
                "mean",
            ),
            event_severity=(
                "event_severity",
                "mean",
            ),
        )
        .reset_index()
    )

    monthly["date"] = (
        monthly["date"].dt.to_timestamp()
    )

    risk_columns = []

    for column in [
        "vix",
        "gpr_index",
        "brent_volatility_30d",
        "wti_volatility_30d",
        "event_severity",
    ]:
        risk_column = f"{column}_risk"

        monthly[risk_column] = minmax_score(
            monthly[column]
        )

        risk_columns.append(risk_column)

    monthly["market_risk_score"] = monthly[
        risk_columns
    ].mean(axis=1)

    return monthly[
        [
            "date",
            "market_risk_score",
        ]
    ]


def prepare_port_risk(congestion):
    """Calculate monthly port congestion risk."""

    congestion = congestion.copy()

    congestion["week_start"] = pd.to_datetime(
        congestion["week_start"],
        errors="coerce",
    )

    congestion = congestion.dropna(
        subset=["week_start"]
    )

    congestion["month"] = (
        congestion["week_start"]
        .dt.to_period("M")
    )

    monthly = (
        congestion.groupby("month")
        .agg(
            congestion_index=(
                "congestion_index",
                "mean",
            ),
            avg_wait_days=(
                "avg_wait_days",
                "mean",
            ),
            vessels_at_anchor=(
                "vessels_at_anchor",
                "mean",
            ),
            port_utilization_pct=(
                "port_utilization_pct",
                "mean",
            ),
        )
        .reset_index()
    )

    monthly["date"] = (
        monthly["month"].dt.to_timestamp()
    )

    risk_columns = []

    for column in [
        "congestion_index",
        "avg_wait_days",
        "vessels_at_anchor",
        "port_utilization_pct",
    ]:
        risk_column = f"{column}_risk"

        monthly[risk_column] = minmax_score(
            monthly[column]
        )

        risk_columns.append(risk_column)

    monthly["port_risk_score"] = monthly[
        risk_columns
    ].mean(axis=1)

    return monthly[
        [
            "date",
            "port_risk_score",
        ]
    ]


def prepare_demand_risk(demand):
    """Calculate static route-level demand risk."""

    demand = demand.copy()

    required_columns = [
        "demand_score",
        "route_priority",
    ]

    if not all(
        column in demand.columns
        for column in required_columns
    ):
        return pd.DataFrame(
            columns=[
                "route_priority",
                "demand_risk_score",
            ]
        )

    demand["demand_score"] = pd.to_numeric(
        demand["demand_score"],
        errors="coerce",
    )

    demand = demand.dropna(
        subset=["demand_score"]
    )

    if demand.empty:
        return pd.DataFrame(
            columns=[
                "route_priority",
                "demand_risk_score",
            ]
        )

    demand["demand_risk_score"] = minmax_score(
        demand["demand_score"],
        higher_is_riskier=False,
    )

    return (
        demand[
            [
                "route_priority",
                "demand_risk_score",
            ]
        ]
        .groupby(
            "route_priority",
            as_index=False,
        )
        .mean()
    )


def prepare_vessel_indicator(vessel):
    """Calculate monthly vessel idle-risk indicators."""

    vessel = vessel.copy()

    if "date" not in vessel.columns:
        if "Date" in vessel.columns:
            vessel = vessel.rename(
                columns={"Date": "date"}
            )

    required_columns = [
        "date",
        "average_load_percentage",
        "turnaround_time_hours",
        "weekly_voyage_count",
    ]

    if not all(
        column in vessel.columns
        for column in required_columns
    ):
        return pd.DataFrame(
            columns=[
                "date",
                "average_load_percentage",
                "turnaround_time_hours",
                "weekly_voyage_count",
                "idle_risk_score",
            ]
        )

    vessel["date"] = pd.to_datetime(
        vessel["date"],
        errors="coerce",
    )

    vessel = vessel.dropna(
        subset=["date"]
    )

    monthly = (
        vessel.groupby(
            vessel["date"].dt.to_period("M")
        )
        .agg(
            average_load_percentage=(
                "average_load_percentage",
                "mean",
            ),
            turnaround_time_hours=(
                "turnaround_time_hours",
                "mean",
            ),
            weekly_voyage_count=(
                "weekly_voyage_count",
                "mean",
            ),
        )
        .reset_index()
    )

    monthly["date"] = (
        monthly["date"].dt.to_timestamp()
    )

    monthly["utilization_score"] = minmax_score(
        monthly["average_load_percentage"],
        higher_is_riskier=False,
    )

    monthly["turnaround_risk"] = minmax_score(
        monthly["turnaround_time_hours"]
    )

    monthly["voyage_activity_score"] = minmax_score(
        monthly["weekly_voyage_count"],
        higher_is_riskier=False,
    )

    monthly["idle_risk_score"] = monthly[
        [
            "utilization_score",
            "turnaround_risk",
            "voyage_activity_score",
        ]
    ].mean(axis=1)

    return monthly[
        [
            "date",
            "average_load_percentage",
            "turnaround_time_hours",
            "weekly_voyage_count",
            "idle_risk_score",
        ]
    ]


def prepare_annual_import_demand(india_imports):
    """
    Calculate annual East Coast bulk-import demand.

    The supplied India import data contains annual
    Period_Start / Period_End periods, so this function
    deliberately performs annual demand analysis.
    """

    imports = india_imports.copy()

    required_columns = [
        "Period_Start",
        "Period_End",
        "Port",
        "Quantity",
        "Unit",
    ]

    if not all(
        column in imports.columns
        for column in required_columns
    ):
        return pd.DataFrame()

    imports["Period_Start"] = pd.to_datetime(
        imports["Period_Start"],
        errors="coerce",
    )

    imports["Period_End"] = pd.to_datetime(
        imports["Period_End"],
        errors="coerce",
    )

    imports["Quantity"] = pd.to_numeric(
        imports["Quantity"],
        errors="coerce",
    )

    imports["Unit"] = (
        imports["Unit"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    imports["Port"] = (
        imports["Port"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    imports = imports.dropna(
        subset=[
            "Period_Start",
            "Period_End",
            "Quantity",
        ]
    )

    imports = imports[
        imports["Unit"].eq("TON")
    ]

    imports = imports[
        imports["Port"].apply(
            is_ocean_port
        )
    ]

    if imports.empty:
        return pd.DataFrame()

    imports["year"] = (
        imports["Period_Start"].dt.year
    )

    # Annual demand by port.
    port_year = (
        imports.groupby(
            [
                "year",
                "Port",
            ],
            as_index=False,
        )
        .agg(
            annual_port_quantity_tons=(
                "Quantity",
                "sum",
            )
        )
    )

    # Total East Coast demand by year.
    annual = (
        port_year.groupby(
            "year",
            as_index=False,
        )
        .agg(
            annual_east_coast_demand_tons=(
                "annual_port_quantity_tons",
                "sum",
            )
        )
    )

    # Historical annual baseline.
    historical_average = (
        annual[
            "annual_east_coast_demand_tons"
        ].mean()
    )

    annual[
        "historical_average_annual_demand_tons"
    ] = historical_average

    annual[
        "annual_demand_ratio"
    ] = np.where(
        historical_average > 0,
        (
            annual[
                "annual_east_coast_demand_tons"
            ]
            / historical_average
        ),
        np.nan,
    )

    # Lower demand = higher risk.
    annual[
        "annual_demand_risk_score"
    ] = (
        1
        - annual[
            "annual_demand_ratio"
        ]
    ).clip(
        lower=0,
        upper=1,
    ) * 100

    annual[
        "annual_demand_risk_level"
    ] = annual[
        "annual_demand_risk_score"
    ].apply(risk_level)

    # Low-demand classification.
    annual[
        "low_demand_period"
    ] = np.select(
        [
            annual[
                "annual_demand_ratio"
            ] < 0.50,

            annual[
                "annual_demand_ratio"
            ] < 0.75,

            annual[
                "annual_demand_ratio"
            ].notna(),
        ],
        [
            "HIGH LOW-DEMAND YEAR",
            "POSSIBLE LOW-DEMAND YEAR",
            "NORMAL DEMAND YEAR",
        ],
        default="UNKNOWN",
    )

    # Highest-demand East Coast port by year.
    best_ports = (
        port_year.sort_values(
            [
                "year",
                "annual_port_quantity_tons",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop_duplicates(
            subset=["year"],
            keep="first",
        )
        .rename(
            columns={
                "Port":
                    "highest_demand_alternative_port",
                "annual_port_quantity_tons":
                    "alternative_port_demand_tons",
            }
        )
    )

    annual = annual.merge(
        best_ports[
            [
                "year",
                "highest_demand_alternative_port",
                "alternative_port_demand_tons",
            ]
        ],
        on="year",
        how="left",
    )

    return annual[
        [
            "year",
            "annual_east_coast_demand_tons",
            "historical_average_annual_demand_tons",
            "annual_demand_ratio",
            "annual_demand_risk_score",
            "annual_demand_risk_level",
            "low_demand_period",
            "highest_demand_alternative_port",
            "alternative_port_demand_tons",
        ]
    ]


def build_analysis():
    """Build the complete Risk + Idle Management analysis."""

    (
        freight,
        market,
        congestion,
        demand,
        vessel,
        india_imports,
    ) = load_data()

    # ---------------------------------------------------------
    # Freight forecast
    # ---------------------------------------------------------

    freight["date"] = pd.to_datetime(
        freight["date"],
        errors="coerce",
    )

    freight = freight.dropna(
        subset=["date"]
    )

    # ---------------------------------------------------------
    # Prepare components
    # ---------------------------------------------------------

    market_risk = prepare_market_risk(
        market
    )

    port_risk = prepare_port_risk(
        congestion
    )

    vessel_indicator = prepare_vessel_indicator(
        vessel
    )

    demand_risk = prepare_demand_risk(
        demand
    )

    annual_import_demand = (
        prepare_annual_import_demand(
            india_imports
        )
    )

    # ---------------------------------------------------------
    # Base result
    # ---------------------------------------------------------

    result = freight[
        [
            "date",
            "predicted_freight_usd_day",
            "freight_attractiveness_score",
        ]
    ].copy()

    # ---------------------------------------------------------
    # Market risk
    # ---------------------------------------------------------

    result = result.merge(
        market_risk,
        on="date",
        how="left",
    )

    # ---------------------------------------------------------
    # Port risk
    # ---------------------------------------------------------

    result = result.merge(
        port_risk,
        on="date",
        how="left",
    )

    # ---------------------------------------------------------
    # Vessel idle risk
    # ---------------------------------------------------------

    result = result.merge(
        vessel_indicator,
        on="date",
        how="left",
    )

    # ---------------------------------------------------------
    # Annual demand context
    # ---------------------------------------------------------

    result["year"] = (
        result["date"].dt.year
    )

    if not annual_import_demand.empty:

        result = result.merge(
            annual_import_demand,
            on="year",
            how="left",
        )

    else:

        result[
            "annual_east_coast_demand_tons"
        ] = np.nan

        result[
            "historical_average_annual_demand_tons"
        ] = np.nan

        result[
            "annual_demand_ratio"
        ] = np.nan

        result[
            "annual_demand_risk_score"
        ] = np.nan

        result[
            "annual_demand_risk_level"
        ] = "UNKNOWN"

        result[
            "low_demand_period"
        ] = "UNKNOWN"

        result[
            "highest_demand_alternative_port"
        ] = "INSUFFICIENT DATA"

        result[
            "alternative_port_demand_tons"
        ] = np.nan

    # ---------------------------------------------------------
    # Overall market + port risk
    # ---------------------------------------------------------

    result[
        "overall_risk_score"
    ] = result[
        [
            "market_risk_score",
            "port_risk_score",
        ]
    ].mean(axis=1)

    result[
        "risk_level"
    ] = result[
        "overall_risk_score"
    ].apply(risk_level)

    # ---------------------------------------------------------
    # Vessel idle-risk level
    # ---------------------------------------------------------

    result[
        "idle_risk_level"
    ] = result[
        "idle_risk_score"
    ].apply(risk_level)

    # ---------------------------------------------------------
    # Data availability
    # ---------------------------------------------------------

    vessel_available = result[
        "idle_risk_score"
    ].notna()

    demand_available = result[
        "annual_demand_risk_score"
    ].notna()

    result[
        "data_availability"
    ] = np.select(
        [
            vessel_available
            & demand_available,

            ~vessel_available
            & demand_available,

            vessel_available
            & ~demand_available,
        ],
        [
            "FULL",
            "DEMAND_ONLY",
            "VESSEL_ONLY",
        ],
        default="INSUFFICIENT_DATA",
    )

    # ---------------------------------------------------------
    # Combined idle + demand risk score
    # ---------------------------------------------------------

    result[
        "combined_idle_demand_risk_score"
    ] = np.where(
        vessel_available
        & demand_available,

        (
            0.60
            * result[
                "idle_risk_score"
            ]
            + 0.40
            * result[
                "annual_demand_risk_score"
            ]
        ),

        np.where(
            ~vessel_available
            & demand_available,

            result[
                "annual_demand_risk_score"
            ],

            np.where(
                vessel_available
                & ~demand_available,

                result[
                    "idle_risk_score"
                ],

                np.nan,
            ),
        ),
    )

    # ---------------------------------------------------------
    # Combined risk level
    #
    # Demand-only months are UNKNOWN because vessel
    # idle risk is not available.
    # ---------------------------------------------------------

    result[
        "combined_idle_demand_risk_level"
    ] = "UNKNOWN"

    full_mask = result[
        "data_availability"
    ].eq("FULL")

    vessel_only_mask = result[
        "data_availability"
    ].eq("VESSEL_ONLY")

    result.loc[
        full_mask,
        "combined_idle_demand_risk_level",
    ] = result.loc[
        full_mask,
        "combined_idle_demand_risk_score",
    ].apply(risk_level)

    result.loc[
        vessel_only_mask,
        "combined_idle_demand_risk_level",
    ] = result.loc[
        vessel_only_mask,
        "combined_idle_demand_risk_score",
    ].apply(risk_level)

    # ---------------------------------------------------------
    # Alternative employment signal
    # ---------------------------------------------------------

    result[
        "alternative_employment_signal"
    ] = np.select(
        [
            (
                full_mask
                & (
                    result[
                        "combined_idle_demand_risk_score"
                    ] >= 66
                )
            ),

            (
                full_mask
                & result[
                    "combined_idle_demand_risk_score"
                ].between(
                    33,
                    65.999999,
                )
            ),

            (
                full_mask
                & (
                    result[
                        "combined_idle_demand_risk_score"
                    ] < 33
                )
            ),

            result[
                "data_availability"
            ].eq("DEMAND_ONLY"),

            result[
                "data_availability"
            ].eq("VESSEL_ONLY"),
        ],
        [
            "CONSIDER ALTERNATIVE EMPLOYMENT",
            "REVIEW EMPLOYMENT OPTIONS",
            "NORMAL UTILIZATION",
            "DEMAND AVAILABLE - VESSEL IDLE RISK UNKNOWN",
            "VESSEL IDLE RISK AVAILABLE - DEMAND UNKNOWN",
        ],
        default="INSUFFICIENT DATA",
    )

    # ---------------------------------------------------------
    # Deadheading risk
    # ---------------------------------------------------------

    result[
        "deadheading_risk"
    ] = "UNKNOWN"

    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] >= 66
        ),
        "deadheading_risk",
    ] = "HIGH"

    result.loc[
        full_mask
        & result[
            "combined_idle_demand_risk_score"
        ].between(
            33,
            65.999999,
        ),
        "deadheading_risk",
    ] = "MEDIUM"

    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] < 33
        ),
        "deadheading_risk",
    ] = "LOW"

    # ---------------------------------------------------------
    # Alternative port availability
    # ---------------------------------------------------------

    has_alternative = (
        result[
            "highest_demand_alternative_port"
        ].notna()
        & ~result[
            "highest_demand_alternative_port"
        ].eq("INSUFFICIENT DATA")
    )

    # ---------------------------------------------------------
    # Positioning action
    # ---------------------------------------------------------

    result[
        "positioning_action"
    ] = (
        "MONITOR DEMAND"
    )

    # FULL + HIGH.
    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] >= 66
        )
        & has_alternative,
        "positioning_action",
    ] = (
        "Reposition early toward the "
        "highest-demand East Coast port "
        "and seek alternative employment."
    )

    # FULL + MEDIUM.
    result.loc[
        full_mask
        & result[
            "combined_idle_demand_risk_score"
        ].between(
            33,
            65.999999,
        )
        & has_alternative,
        "positioning_action",
    ] = (
        "Monitor cargo demand and consider "
        "positioning toward the highest-demand "
        "East Coast port."
    )

    # FULL + LOW.
    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] < 33
        ),
        "positioning_action",
    ] = (
        "Maintain current positioning; "
        "no immediate repositioning required."
    )

    # DEMAND ONLY.
    result.loc[
        result[
            "data_availability"
        ].eq("DEMAND_ONLY"),
        "positioning_action",
    ] = (
        "Demand data is available. "
        "Monitor vessel status before "
        "repositioning toward the "
        "highest-demand East Coast port."
    )

    # VESSEL ONLY.
    result.loc[
        result[
            "data_availability"
        ].eq("VESSEL_ONLY"),
        "positioning_action",
    ] = (
        "Vessel idle risk is available, "
        "but demand data is unavailable. "
        "Monitor cargo demand before repositioning."
    )

    # ---------------------------------------------------------
    # Idle-management recommendation
    # ---------------------------------------------------------

    result[
        "idle_management_recommendation"
    ] = (
        "Insufficient vessel and demand data; "
        "monitor before repositioning."
    )

    # FULL + HIGH + alternative.
    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] >= 66
        )
        & has_alternative,
        "idle_management_recommendation",
    ] = (
        "High idle/demand risk. Prioritize "
        "alternative employment and reposition "
        "toward the strongest-demand East Coast "
        "port to reduce idle time and deadheading."
    )

    # FULL + HIGH without alternative.
    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] >= 66
        )
        & ~has_alternative,
        "idle_management_recommendation",
    ] = (
        "High idle/demand risk. Seek alternative "
        "employment before the vessel becomes idle."
    )

    # FULL + MEDIUM.
    result.loc[
        full_mask
        & result[
            "combined_idle_demand_risk_score"
        ].between(
            33,
            65.999999,
        ),
        "idle_management_recommendation",
    ] = (
        "Moderate idle/demand risk. Monitor demand "
        "and prepare alternative employment."
    )

    # FULL + LOW.
    result.loc[
        full_mask
        & (
            result[
                "combined_idle_demand_risk_score"
            ] < 33
        ),
        "idle_management_recommendation",
    ] = (
        "Low idle/demand risk. Continue current "
        "employment and positioning."
    )

    # DEMAND ONLY.
    result.loc[
        result[
            "data_availability"
        ].eq("DEMAND_ONLY"),
        "idle_management_recommendation",
    ] = (
        "Demand data is available, but vessel "
        "idle-risk data is unavailable. "
        "Monitor vessel utilization before "
        "making repositioning decisions."
    )

    # VESSEL ONLY.
    result.loc[
        result[
            "data_availability"
        ].eq("VESSEL_ONLY"),
        "idle_management_recommendation",
    ] = (
        "Vessel idle-risk data is available, "
        "but cargo demand data is unavailable. "
        "Monitor demand before seeking "
        "alternative employment."
    )

    # ---------------------------------------------------------
    # Static route-demand risk
    # ---------------------------------------------------------

    if not demand_risk.empty:

        route_demand_risk_score = (
            demand_risk[
                "demand_risk_score"
            ].mean()
        )

    else:

        route_demand_risk_score = np.nan

    result[
        "route_demand_risk_score"
    ] = route_demand_risk_score

    result[
        "route_demand_risk_level"
    ] = risk_level(
        route_demand_risk_score
    )

    # ---------------------------------------------------------
    # Remove temporary year
    # ---------------------------------------------------------

    result = result.drop(
        columns=["year"]
    )

    # ---------------------------------------------------------
    # Final column order
    # ---------------------------------------------------------

    preferred_columns = [
        "date",

        "predicted_freight_usd_day",
        "freight_attractiveness_score",

        "market_risk_score",
        "port_risk_score",
        "overall_risk_score",
        "risk_level",

        "average_load_percentage",
        "turnaround_time_hours",
        "weekly_voyage_count",

        "idle_risk_score",
        "idle_risk_level",
        "data_availability",

        "annual_east_coast_demand_tons",
        "historical_average_annual_demand_tons",
        "annual_demand_ratio",
        "annual_demand_risk_score",
        "annual_demand_risk_level",
        "low_demand_period",

        "combined_idle_demand_risk_score",
        "combined_idle_demand_risk_level",

        "route_demand_risk_score",
        "route_demand_risk_level",

        "alternative_employment_signal",
        "deadheading_risk",

        "highest_demand_alternative_port",
        "alternative_port_demand_tons",

        "positioning_action",
        "idle_management_recommendation",
    ]

    result = result[
        [
            column
            for column in preferred_columns
            if column in result.columns
        ]
    ]

    return result


def main():
    """Run Risk + Idle Management and save the result."""

    result = build_analysis()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print(
        "\nRisk + Idle Management completed."
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        f"Rows: {len(result)}"
    )

    print("\nData availability:")

    print(
        result[
            "data_availability"
        ].value_counts(
            dropna=False
        )
    )

    print("\nLatest results:")

    print(
        result.tail(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()