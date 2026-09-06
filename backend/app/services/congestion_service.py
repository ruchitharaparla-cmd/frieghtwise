from typing import Optional


def calculate_congestion_score(
    average_waiting_hours: Optional[float],
) -> dict:
    if average_waiting_hours is None:
        return {
            "score": None,
            "impact": "UNKNOWN",
            "data_status": "UNAVAILABLE",
        }

    if average_waiting_hours <= 12:
        score = 20
        impact = "LOW"
    elif average_waiting_hours <= 36:
        score = 50
        impact = "MEDIUM"
    else:
        score = 80
        impact = "HIGH"

    return {
        "score": score,
        "impact": impact,
        "data_status": "KNOWN",
    }


def estimate_delay_hours(
    average_waiting_hours: Optional[float],
) -> Optional[float]:
    if average_waiting_hours is None:
        return None

    return max(0.0, average_waiting_hours)