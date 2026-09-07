from datetime import date

from app.core.database import SessionLocal
from app.models.vessel import Vessel
from app.models.port import Port
from app.models.freight import Freight


db = SessionLocal()

try:
    # -------------------------
    # DEMO VESSELS
    # -------------------------
    vessels = [
        Vessel(
            name="DEMO BULK 01",
            vessel_class="Bulk Carrier",
            dwt=80000,
            loa_m=225,
            beam_m=32,
            draft_m=13.5,
            cargo_types="Coal,Iron Ore,Grain",
            is_available=True,
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
        Vessel(
            name="DEMO BULK 02",
            vessel_class="Bulk Carrier",
            dwt=60000,
            loa_m=200,
            beam_m=30,
            draft_m=12.0,
            cargo_types="Coal,Iron Ore,Grain",
            is_available=True,
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
        Vessel(
            name="DEMO TANKER 01",
            vessel_class="Tanker",
            dwt=90000,
            loa_m=230,
            beam_m=35,
            draft_m=14.0,
            cargo_types="Crude Oil,Palm Oil",
            is_available=True,
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
    ]

    # -------------------------
    # DEMO PORTS
    # -------------------------
    ports = [
        Port(
            name="Demo Visakhapatnam",
            code="DEMO-VIZ",
            state="Andhra Pradesh",
            country="India",
            latitude=17.6868,
            longitude=83.2185,
            max_draft_m=16.0,
            max_loa_m=250,
            max_beam_m=40,
            annual_capacity_tonnes=80000000,
            utilization_percent=65,
            average_waiting_hours=18,
            cargo_types="Coal,Iron Ore,Grain",
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
        Port(
            name="Demo Gangavaram",
            code="DEMO-GANG",
            state="Andhra Pradesh",
            country="India",
            latitude=17.5895,
            longitude=83.2370,
            max_draft_m=18.0,
            max_loa_m=300,
            max_beam_m=45,
            annual_capacity_tonnes=60000000,
            utilization_percent=55,
            average_waiting_hours=10,
            cargo_types="Coal,Iron Ore",
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
        Port(
            name="Demo Paradip",
            code="DEMO-PARA",
            state="Odisha",
            country="India",
            latitude=20.2644,
            longitude=86.6114,
            max_draft_m=16.5,
            max_loa_m=280,
            max_beam_m=42,
            annual_capacity_tonnes=100000000,
            utilization_percent=70,
            average_waiting_hours=30,
            cargo_types="Coal,Iron Ore,Grain",
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
    ]

    # -------------------------
    # DEMO FREIGHT RATES
    # -------------------------
    freight_rates = [
        Freight(
            origin_country="Australia",
            destination_region="East Coast India",
            cargo_type="Coal",
            vessel_class="Bulk Carrier",
            forecast_date=date(2026, 9, 20),
            freight_rate=25.0,
            currency="USD",
            unit="per_metric_tonne",
            model_version="DEMO",
            confidence=0.80,
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
        Freight(
            origin_country="Indonesia",
            destination_region="East Coast India",
            cargo_type="Coal",
            vessel_class="Bulk Carrier",
            forecast_date=date(2026, 9, 20),
            freight_rate=22.0,
            currency="USD",
            unit="per_metric_tonne",
            model_version="DEMO",
            confidence=0.80,
            data_status="ESTIMATED",
            source="DEMO_ONLY_FOR_DEVELOPMENT",
        ),
    ]

    db.add_all(vessels)
    db.add_all(ports)
    db.add_all(freight_rates)

    db.commit()

    print("Demo data inserted successfully.")
    print(f"Vessels added: {len(vessels)}")
    print(f"Ports added: {len(ports)}")
    print(f"Freight records added: {len(freight_rates)}")

finally:
    db.close()
