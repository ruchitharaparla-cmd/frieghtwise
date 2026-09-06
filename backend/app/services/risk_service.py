from typing import Optional


def calculate_risk(
    congestion_score: Optional[float],
    weather_score: Optional[float] = None,
    demurrage_score: Optional[float] = None,
) -> dict:
    scores = [
        score
        for score in (
            congestion_score,
            weather_score,
            demurrage_score,
        )
        if score is not None
    ]

    if not scores:
        return {
            "overall_risk": None,
            "risk_level": "HIGH",
            "factors": {
                "congestion": {
                    "score": None,
                    "impact": "UNKNOWN",
                },
                "weather": {
                    "score": None,
                    "impact": "UNKNOWN",
                },
                "demurrage": {
                    "score": None,
                    "impact": "UNKNOWN",
                },
            },
            "data_status": "UNAVAILABLE",
        }

    overall_risk = sum(scores) / len(scores)

    if overall_risk < 35:
        risk_level = "LOW"
    elif overall_risk < 65:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    def get_impact(score: Optional[float]) -> str:
        if score is None:
            return "UNKNOWN"
        if score < 35:
            return "LOW"
        if score < 65:
            return "MEDIUM"
        return "HIGH"

    return {
        "overall_risk": round(overall_risk, 2),
        "risk_level": risk_level,
        "factors": {
            "congestion": {
                "score": congestion_score,
                "impact": get_impact(congestion_score),
            },
            "weather": {
                "score": weather_score,
                "impact": get_impact(weather_score),
            },
            "demurrage": {
                "score": demurrage_score,
                "impact": get_impact(demurrage_score),
            },
        },
        "data_status": "KNOWN",
    }