from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db import models

router = APIRouter()


@router.get("/")
def list_devices(db: Session = Depends(get_db)):
    return db.query(models.Device).all()


@router.get("/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter_by(device_id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/{device_id}/isolate")
def manual_isolate(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter_by(device_id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_isolated = True
    db.commit()
    return {"status": "isolated", "device_id": device_id}


@router.post("/{device_id}/restore")
def restore_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter_by(device_id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_isolated = False
    db.commit()
    return {"status": "restored", "device_id": device_id}
