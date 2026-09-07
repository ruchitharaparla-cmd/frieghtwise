def calculate_risk(
    congestion_score,
    weather_score=None,
    demurrage_score=None,
    data_status="KNOWN",
):
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

    if congestion_score is None:
        congestion_impact = "UNKNOWN"
    elif congestion_score < 35:
        congestion_impact = "LOW"
    elif congestion_score < 65:
        congestion_impact = "MEDIUM"
    else:
        congestion_impact = "HIGH"

    if weather_score is None:
        weather_impact = "UNKNOWN"
    elif weather_score < 35:
        weather_impact = "LOW"
    elif weather_score < 65:
        weather_impact = "MEDIUM"
    else:
        weather_impact = "HIGH"

    if demurrage_score is None:
        demurrage_impact = "UNKNOWN"
    elif demurrage_score < 35:
        demurrage_impact = "LOW"
    elif demurrage_score < 65:
        demurrage_impact = "MEDIUM"
    else:
        demurrage_impact = "HIGH"

    return {
        "overall_risk": round(overall_risk, 2),
        "risk_level": risk_level,
        "factors": {
            "congestion": {
                "score": congestion_score,
                "impact": congestion_impact,
            },
            "weather": {
                "score": weather_score,
                "impact": weather_impact,
            },
            "demurrage": {
                "score": demurrage_score,
                "impact": demurrage_impact,
            },
        },
        "data_status": data_status,
    }