from dataclasses import dataclass
from typing import List, Dict

from src.decision.vessel_port_feasibility import (
    VesselInput,
    load_ports,
    check_vessel_port,
)


@dataclass
class VesselCandidate:
    vessel_name: str
    vessel_type: str
    dwt_tons: float
    loa_m: float
    beam_m: float
    draft_m: float
    speed_knots: float = 12.0


def calculate_vessel_suitability(
    vessel: VesselCandidate,
    cargo_tons: float,
    feasibility_score: float,
) -> float:

    if cargo_tons <= 0:
        raise ValueError("cargo_tons must be positive")

    if vessel.dwt_tons <= 0:
        raise ValueError("vessel dwt_tons must be positive")

    utilization = cargo_tons / vessel.dwt_tons

    if utilization > 1:
        cargo_score = 0.0
    elif utilization >= 0.70:
        cargo_score = 100.0
    elif utilization >= 0.50:
        cargo_score = 80.0
    elif utilization >= 0.30:
        cargo_score = 60.0
    else:
        cargo_score = 40.0

    speed_score = min(
        max((vessel.speed_knots / 14.0) * 100, 0),
        100,
    )

    score = (
        feasibility_score * 0.60
        + cargo_score * 0.30
        + speed_score * 0.10
    )

    return round(score, 2)


def optimize_vessel_type(
    cargo_tons: float,
    port_name: str,
    candidates: List[VesselCandidate],
) -> Dict:

    if cargo_tons <= 0:
        raise ValueError("cargo_tons must be positive")

    if not candidates:
        raise ValueError("At least one vessel candidate is required")

    ports = load_ports()

    port_matches = ports[
        ports["name"].astype(str).str.lower()
        == port_name.lower()
    ]

    if port_matches.empty:
        raise ValueError(
            f"Port '{port_name}' not found in port dataset"
        )

    port_row = port_matches.iloc[0]

    results = []

    for candidate in candidates:

        vessel = VesselInput(
            vessel_name=candidate.vessel_name,
            vessel_type=candidate.vessel_type,
            dwt_tons=candidate.dwt_tons,
            loa_m=candidate.loa_m,
            beam_m=candidate.beam_m,
            draft_m=candidate.draft_m,
        )

        feasibility = check_vessel_port(
            vessel,
            port_row,
        )

        feasible = feasibility["status"] == "FEASIBLE"

        if feasible:
            suitability_score = calculate_vessel_suitability(
                candidate,
                cargo_tons,
                feasibility["feasibility_score"],
            )
        else:
            suitability_score = 0.0

        results.append(
            {
                "vessel_name": candidate.vessel_name,
                "vessel_type": candidate.vessel_type,
                "dwt_tons": candidate.dwt_tons,
                "cargo_tons": cargo_tons,
                "cargo_utilization_percent": round(
                    min(
                        cargo_tons / candidate.dwt_tons * 100,
                        100,
                    ),
                    2,
                ),
                "port_name": port_name,
                "feasibility_status": feasibility["status"],
                "feasibility_score": feasibility["feasibility_score"],
                "feasibility_reason": feasibility["reason"],
                "suitability_score": suitability_score,
                "port_data_status": feasibility["port_data_status"],
            }
        )

    feasible_results = [
        result
        for result in results
        if result["feasibility_status"] == "FEASIBLE"
    ]

    if feasible_results:
        recommended = max(
            feasible_results,
            key=lambda result: result["suitability_score"],
        )
        recommendation = recommended["vessel_type"]
    else:
        recommended = None
        recommendation = "NO FEASIBLE VESSEL"

    return {
        "cargo_tons": cargo_tons,
        "port_name": port_name,
        "recommendation": recommendation,
        "recommended_vessel": recommended,
        "candidates": sorted(
            results,
            key=lambda result: result["suitability_score"],
            reverse=True,
        ),
    }


if __name__ == "__main__":

    # Synthetic test candidates only.
    candidates = [
        VesselCandidate(
            vessel_name="Handysize Candidate",
            vessel_type="Handysize",
            dwt_tons=40000,
            loa_m=180,
            beam_m=30,
            draft_m=11,
        ),
        VesselCandidate(
            vessel_name="Supramax Candidate",
            vessel_type="Supramax",
            dwt_tons=60000,
            loa_m=200,
            beam_m=32,
            draft_m=12,
        ),
        VesselCandidate(
            vessel_name="Panamax Candidate",
            vessel_type="Panamax",
            dwt_tons=75000,
            loa_m=225,
            beam_m=32,
            draft_m=13,
        ),
        VesselCandidate(
            vessel_name="Capesize Candidate",
            vessel_type="Capesize",
            dwt_tons=180000,
            loa_m=290,
            beam_m=45,
            draft_m=17,
        ),
    ]

    result = optimize_vessel_type(
        cargo_tons=70000,
        port_name="Paradip Port",
        candidates=candidates,
    )

    print("\n=== VESSEL TYPE OPTIMIZATION ===")
    print("Cargo:", result["cargo_tons"], "tonnes")
    print("Port:", result["port_name"])
    print("Recommendation:", result["recommendation"])

    print("\nCandidate comparison:")

    for candidate in result["candidates"]:
        print(
            f"{candidate['vessel_type']} -> "
            f"{candidate['feasibility_status']} -> "
            f"Suitability: {candidate['suitability_score']}"
        )

        print(
            f"  Cargo utilization: "
            f"{candidate['cargo_utilization_percent']}%"
        )

        print(
            f"  Feasibility score: "
            f"{candidate['feasibility_score']}"
        )

        print(
            f"  Reason: "
            f"{candidate['feasibility_reason']}"
        )