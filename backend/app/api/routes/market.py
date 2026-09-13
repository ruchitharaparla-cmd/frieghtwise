from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.freight import Freight
from app.schemas.market import (
    FreightTrendPoint,
    FreightTrendResponse,
    FreightTrendRoute,
    FreightTrendSource,
)


router = APIRouter(tags=["Market"])


OBSERVED_STATUSES = {
    "ACTUAL",
    "OBSERVED",
    "HISTORICAL",
}

FORECAST_STATUSES = {
    "FORECAST",
    "PREDICTED",
    "PREDICTION",
}


def normalize_value_type(status: str | None) -> str:
    """
    Convert database status values into frontend-friendly values.
    """
    normalized_status = (status or "UNKNOWN").strip().upper()

    if normalized_status in OBSERVED_STATUSES:
        return "OBSERVED"

    if normalized_status in FORECAST_STATUSES:
        return "FORECAST"

    return "UNKNOWN"


def normalize_data_status(statuses: set[str]) -> str:
    """
    Convert database statuses into the API-level data status.
    """
    if statuses.intersection(OBSERVED_STATUSES):
        return "AVAILABLE"

    if statuses.intersection(FORECAST_STATUSES):
        return "FORECAST"

    return "UNKNOWN"


@router.get(
    "/market/freight-trend",
    response_model=FreightTrendResponse,
)
def get_freight_trend(
    origin_country: str = Query(..., min_length=1),
    destination_region: str = Query(..., min_length=1),
    cargo_type: str = Query(..., min_length=1),
    vessel_class: str = Query(..., min_length=1),
    days: int = Query(
        default=7,
        ge=2,
        le=90,
    ),
    db: Session = Depends(get_db),
):
    """
    Return historical and/or forecast freight-rate trend data
    for a selected route, cargo type, and vessel class.

    The dataset contains monthly records. Therefore, the endpoint
    compares the latest observation with the immediately previous
    observation instead of using a calendar-day window.
    """

    route = FreightTrendRoute(
        origin_country=origin_country,
        destination_region=destination_region,
        display_name=(
            f"{origin_country} → {destination_region}"
        ),
    )

    records = (
        db.query(Freight)
        .filter(
            Freight.origin_country == origin_country,
            Freight.destination_region == destination_region,
            Freight.cargo_type == cargo_type,
            Freight.vessel_class == vessel_class,
            Freight.freight_rate.isnot(None),
        )
        .order_by(Freight.forecast_date.asc())
        .all()
    )

    if not records:
        return FreightTrendResponse(
            data_status="UNAVAILABLE",
            route=route,
            trend=[],
            source=FreightTrendSource(
                name=None,
                data_status="UNKNOWN",
            ),
            message=(
                "No freight-rate records were found for "
                "the selected route, cargo type, and vessel class."
            ),
        )

    # Keep one record per date.
    # If duplicate records exist for the same date, the later
    # record encountered in the query result replaces the earlier one.
    records_by_date = {}

    for record in records:
        records_by_date[record.forecast_date] = record

    unique_records = [
        records_by_date[record_date]
        for record_date in sorted(records_by_date)
    ]

    if not unique_records:
        return FreightTrendResponse(
            data_status="UNAVAILABLE",
            route=route,
            trend=[],
            source=FreightTrendSource(
                name=None,
                data_status="UNKNOWN",
            ),
            message="No usable freight-rate values were found.",
        )

    # The frontend currently sends days=7.
    # Since the database contains monthly records, use the latest
    # available observations rather than filtering by calendar days.
    #
    # Keep the latest 7 observations for the chart.
    chart_records = unique_records[-days:]

    trend = [
        FreightTrendPoint(
            date=record.forecast_date,
            rate=float(record.freight_rate),
            value_type=normalize_value_type(
                record.data_status
            ),
        )
        for record in chart_records
    ]

    if not trend:
        return FreightTrendResponse(
            data_status="UNAVAILABLE",
            route=route,
            trend=[],
            source=FreightTrendSource(
                name=None,
                data_status="UNKNOWN",
            ),
            message="No usable freight-rate values were found.",
        )

    # Latest available rate.
    current_rate = trend[-1].rate

    # Compare the latest observation with the immediately previous
    # observation, regardless of whether records are daily, weekly,
    # or monthly.
    if len(unique_records) >= 2:
        previous_rate = float(unique_records[-2].freight_rate)

        if previous_rate == 0:
            change_7d = None
        else:
            change_7d = round(
                (
                    (current_rate - previous_rate)
                    / previous_rate
                )
                * 100,
                2,
            )
    else:
        previous_rate = None
        change_7d = None

    if change_7d is None:
        market_direction = "UNKNOWN"
    elif change_7d > 0:
        market_direction = "BULLISH"
    elif change_7d < 0:
        market_direction = "BEARISH"
    else:
        market_direction = "STABLE"

    latest_record = unique_records[-1]

    statuses = {
        (record.data_status or "UNKNOWN").strip().upper()
        for record in chart_records
    }

    data_status = normalize_data_status(statuses)

    source_status = normalize_value_type(
        latest_record.data_status
    )

    return FreightTrendResponse(
        data_status=data_status,
        currency=latest_record.currency or "USD",
        unit=latest_record.unit or "per_metric_tonne",
        route=route,
        current_rate=current_rate,
        previous_rate=previous_rate,
        change_7d=change_7d,
        market_direction=market_direction,
        trend=trend,
        source=FreightTrendSource(
            name=latest_record.source,
            data_status=source_status,
        ),
        message=None,
    )