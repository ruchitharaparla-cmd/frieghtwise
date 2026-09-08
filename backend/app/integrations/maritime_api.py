from datetime import date
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


class MaritimeProviderError(Exception):
    """Raised when the maritime data provider is unavailable."""


def get_vessel_position(
    vessel_id: int,
    target_date: date,
) -> dict[str, Any]:
    """
    Retrieve maritime position information for a vessel.

    The current prototype does not claim live AIS data because
    no external AIS provider has been configured yet.
    """

    return {
        "data_status": "UNAVAILABLE",
        "source": "AIS provider not configured",
        "vessel_id": vessel_id,
        "target_date": target_date,
        "message": (
            "Live maritime/AIS data is not configured. "
            "FreightWise will not fabricate vessel position data."
        ),
    }


def get_vessel_eta(
    vessel_id: int,
    target_date: date,
) -> dict[str, Any]:
    """
    Retrieve ETA information for a vessel.

    Returns unavailable until a real maritime/AIS provider
    is connected.
    """

    return {
        "data_status": "UNAVAILABLE",
        "source": "AIS provider not configured",
        "vessel_id": vessel_id,
        "target_date": target_date,
        "eta": None,
        "message": (
            "Live vessel ETA data is not configured. "
            "No ETA has been inferred or fabricated."
        ),
    }


def get_port_vessel_activity(
    port_id: int,
    target_date: date,
) -> dict[str, Any]:
    """
    Retrieve vessel activity information for a port.

    This is intentionally unavailable until a real maritime
    data provider is connected.
    """

    return {
        "data_status": "UNAVAILABLE",
        "source": "AIS provider not configured",
        "port_id": port_id,
        "target_date": target_date,
        "arrivals": None,
        "departures": None,
        "vessels_in_port": None,
        "message": (
            "Live port vessel activity is not configured. "
            "FreightWise will not fabricate maritime activity."
        ),
    }