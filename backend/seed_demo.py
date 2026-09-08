from app.core.database import SessionLocal
from app.models.vessel import Vessel
from app.models.port import Port


db = SessionLocal()

try:
    # ---------------------------------------------------------
    # REMOVE ONLY THE CURRENT DEVELOPMENT SEED RECORDS
    # ---------------------------------------------------------
    db.query(Vessel).filter(
        Vessel.source == "DEMO_ONLY_FOR_DEVELOPMENT"
    ).delete(synchronize_session=False)

    db.query(Port).filter(
        Port.source == "DEMO_ONLY_FOR_DEVELOPMENT"
    ).delete(synchronize_session=False)

    # ---------------------------------------------------------
    # REFERENCE VESSEL CLASSES
    #
    # These are vessel-class specifications, NOT live vessels.
    # They must not be interpreted as actual charter availability.
    # ---------------------------------------------------------
    vessels = [
        Vessel(
            id=1,
            name="REFERENCE KAMSARMAX",
            vessel_class="Kamsarmax",
            dwt=82400,
            loa_m=229.0,
            beam_m=32.26,
            draft_m=14.55,
            cargo_types="Coal,Iron Ore,Grain",
            is_available=True,
            data_status="REFERENCE",
            source="TSUNEISHI_KAMSARMAX_SPECIFICATION",
        ),
        Vessel(
            id=2,
            name="REFERENCE PANAMAX",
            vessel_class="Panamax",
            dwt=76000,
            loa_m=225.0,
            beam_m=32.0,
            draft_m=14.0,
            cargo_types="Coal,Iron Ore,Grain",
            is_available=True,
            data_status="REFERENCE",
            source="BALTIC_EXCHANGE_VESSEL_CLASS_REFERENCE",
        ),
        Vessel(
            id=3,
            name="REFERENCE CAPESIZE",
            vessel_class="Capesize",
            dwt=150000,
            loa_m=292.0,
            beam_m=45.0,
            draft_m=16.5,
            cargo_types="Coal,Iron Ore,Grain",
            is_available=True,
            data_status="REFERENCE",
            source="BALTIC_EXCHANGE_AND_PORT_CAPABILITY_REFERENCE",
        ),
    ]

    # ---------------------------------------------------------
    # PORT REFERENCE DATA
    #
    # Dimensions are representative dry-bulk operating limits
    # derived from published berth-level information.
    #
    # They are NOT universal limits for every berth in the port.
    # ---------------------------------------------------------
    ports = [
        Port(
            id=1,
            name="Visakhapatnam Port",
            code="INVTZ",
            state="Andhra Pradesh",
            country="India",
            latitude=17.6868,
            longitude=83.2185,
            max_draft_m=16.5,
            max_loa_m=300.0,
            max_beam_m=50.0,
            annual_capacity_tonnes=154710000,
            utilization_percent=53.41,
            average_waiting_hours=23.55,
            cargo_types="Coal,Iron Ore,Grain",
            data_status="REFERENCE",
            source="VISAKHAPATNAM_PORT_AUTHORITY_BERTH_DATA",
        ),
        Port(
            id=2,
            name="Gangavaram Port",
            code="INGGV",
            state="Andhra Pradesh",
            country="India",
            latitude=17.5895,
            longitude=83.2370,
            max_draft_m=18.0,
            max_loa_m=300.0,
            max_beam_m=45.0,
            annual_capacity_tonnes=60000000,
            utilization_percent=None,
            average_waiting_hours=None,
            cargo_types="Coal,Iron Ore",
            data_status="REFERENCE",
            source="GANGAVARAM_PORT_BERTH_DATA",
        ),
        Port(
            id=3,
            name="Paradip Port",
            code="INPRT",
            state="Odisha",
            country="India",
            latitude=20.2644,
            longitude=86.6114,
            max_draft_m=16.0,
            max_loa_m=300.0,
            max_beam_m=46.0,
            annual_capacity_tonnes=None,
            utilization_percent=None,
            average_waiting_hours=None,
            cargo_types="Coal,Iron Ore,Grain",
            data_status="REFERENCE",
            source="PARADIP_PORT_AUTHORITY_BERTH_DATA",
        ),
    ]

    db.add_all(vessels)
    db.add_all(ports)

    db.commit()

    print("Reference data seeded successfully.")
    print(f"Vessels added: {len(vessels)}")
    print(f"Ports added: {len(ports)}")
    print()
    print("IMPORTANT:")
    print("- Vessel records represent reference vessel classes.")
    print("- They are not live charter availability.")
    print("- Port dimensions are representative berth-derived limits.")
    print("- Missing operational values remain NULL rather than being fabricated.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
