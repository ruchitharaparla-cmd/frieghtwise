import csv
from datetime import datetime

from app.core.database import SessionLocal
from app.models.freight import Freight


CSV_PATH = "../data/processed/freight_rates_indian_east_coast.csv"


def parse_date(value):
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def clean_optional(value):
    value = value.strip()
    if value.upper() in {"N/A", "NA", ""}:
        return None
    return value


def import_freight_rates():
    db = SessionLocal()

    try:
        # Remove existing freight-rate records
        deleted = db.query(Freight).delete()
        print(f"Deleted existing freight-rate records: {deleted}")

        inserted = 0

        with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                vessel_class = row["Vessel class"].strip()

                # Normalize vessel classes
                if "Panamax" in vessel_class:
                    vessel_class = "Bulk Carrier"
                elif "VLOC" in vessel_class:
                    vessel_class = "Bulk Carrier"
                elif (
                    "VLCC" in vessel_class
                    or "Suezmax" in vessel_class
                    or "MR Tanker" in vessel_class
                ):
                    vessel_class = "Tanker"

                unit = row["Unit"].strip()

                # Match backend's expected unit
                if unit.lower() == "metric ton":
                    unit = "per_metric_tonne"

                freight = Freight(
                    origin_country=row["Origin country"].strip(),
                    destination_region=row["Destination region"].strip(),
                    cargo_type=row["Cargo type"].strip(),
                    vessel_class=vessel_class,
                    forecast_date=parse_date(
                        row["Date / forecast date"]
                    ),
                    freight_rate=float(row["Freight rate"]),
                    currency=row["Currency"].strip(),
                    unit=unit,
                    model_version=clean_optional(
                        row["Model version"]
                    ),
                    confidence=(
                        float(row["Confidence"])
                        if clean_optional(row["Confidence"])
                        else None
                    ),
                    data_status=row["Data status"].strip(),
                    source=row["Source"].strip(),
                )

                db.add(freight)
                inserted += 1

        db.commit()

        print(f"Successfully inserted freight-rate records: {inserted}")

    except Exception as exc:
        db.rollback()
        print(f"Import failed: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_freight_rates()