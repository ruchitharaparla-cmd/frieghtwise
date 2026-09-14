from dataclasses import dataclass
from pathlib import Path
import pandas as pd


PORT_FILE = Path("data/processed/port_details_estimated.csv")


@dataclass
class VesselInput:
    vessel_name: str
    vessel_type: str
    dwt_tons: float
    loa_m: float
    beam_m: float
    draft_m: float


def load_ports():
    if not PORT_FILE.exists():
        raise FileNotFoundError(
            f"Port dataset not found: {PORT_FILE}"
        )

    df = pd.read_csv(PORT_FILE)

    required = [
        "name",
        "max_loa_m",
        "max_beam_m",
        "max_draft_m",
        "data_status",
    ]

    missing = [
        column for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing port columns: {missing}"
        )

    return df


def check_vessel_port(vessel: VesselInput, port_row):
    checks = {
        "loa": vessel.loa_m <= port_row["max_loa_m"],
        "beam": vessel.beam_m <= port_row["max_beam_m"],
        "draft": vessel.draft_m <= port_row["max_draft_m"],
    }

    passed = sum(checks.values())
    total = len(checks)

    if passed == total:
        status = "FEASIBLE"
    else:
        status = "NOT FEASIBLE"

    reasons = []

    if not checks["loa"]:
        reasons.append(
            f"LOA {vessel.loa_m}m exceeds "
            f"limit {port_row['max_loa_m']}m"
        )

    if not checks["beam"]:
        reasons.append(
            f"Beam {vessel.beam_m}m exceeds "
            f"limit {port_row['max_beam_m']}m"
        )

    if not checks["draft"]:
        reasons.append(
            f"Draft {vessel.draft_m}m exceeds "
            f"limit {port_row['max_draft_m']}m"
        )

    if not reasons:
        reasons.append(
            "Vessel dimensions satisfy available "
            "port limits."
        )

    return {
        "port": port_row["name"],
        "vessel": vessel.vessel_name,
        "vessel_type": vessel.vessel_type,
        "status": status,
        "loa_check": checks["loa"],
        "beam_check": checks["beam"],
        "draft_check": checks["draft"],
        "feasibility_score": (
            passed / total * 100
        ),
        "port_data_status": port_row["data_status"],
        "reason": "; ".join(reasons),
    }


def evaluate_vessel(
    vessel: VesselInput,
    port_name: str | None = None,
):
    ports = load_ports()

    if port_name:
        matches = ports[
            ports["name"].str.contains(
                port_name,
                case=False,
                na=False,
            )
        ]

        if matches.empty:
            raise ValueError(
                f"Port not found: {port_name}"
            )

        ports = matches

    results = []

    for _, port in ports.iterrows():
        results.append(
            check_vessel_port(vessel, port)
        )

    return pd.DataFrame(results)


def main():
    print("Vessel + Port Feasibility module loaded.")

    # Example vessel input for testing only.
    # Replace these values with verified vessel
    # specifications when used in production.
    vessel = VesselInput(
        vessel_name="Example Vessel",
        vessel_type="Panamax",
        dwt_tons=75000,
        loa_m=225,
        beam_m=32,
        draft_m=13,
    )

    result = evaluate_vessel(vessel)

    print("\nFeasibility results:")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()