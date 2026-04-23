"""
Run once before starting the app to pre-populate device registry.
Usage (from backend/): python ../scripts/seed_devices.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from db.database import init_db, SessionLocal
from db.models import Device

DEVICES = [
    {"device_id": "device-01", "device_type": "power_plant",    "location": "Zone-A"},
    {"device_id": "device-02", "device_type": "water_treatment", "location": "Zone-B"},
    {"device_id": "device-03", "device_type": "factory",         "location": "Zone-C"},
]

def seed():
    init_db()
    db = SessionLocal()
    try:
        for d in DEVICES:
            if not db.query(Device).filter_by(device_id=d["device_id"]).first():
                db.add(Device(**d))
                print(f"[SEED] Added {d['device_id']}")
            else:
                print(f"[SEED] Already exists: {d['device_id']}")
        db.commit()
        print("[SEED] Done.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
