import json
import time
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
import paho.mqtt.client as mqtt

from core.config import settings
from mqtt import simulator

router = APIRouter()


class AttackInjectionRequest(BaseModel):
    device_id: str
    attack_type: Literal["DoS", "Spoofing", "Replay", "PhysicalTamper"]


@router.post("/inject-attack")
def inject_attack(payload: AttackInjectionRequest):
    simulator.inject_attack(payload.device_id, payload.attack_type)
    device = next((d for d in simulator.DEVICES if d["id"] == payload.device_id), None)
    telemetry_payload = simulator._build_payload(device) if device else None
    simulator.inject_attack(payload.device_id, None)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
    client.loop_start()
    result = client.publish(
        f"{settings.MQTT_TOPIC_COMMANDS}/{payload.device_id}",
        json.dumps({
            "action": "INJECT_ATTACK",
            "device_id": payload.device_id,
            "attack_type": payload.attack_type,
        }),
        qos=1,
    )
    result.wait_for_publish(timeout=2.0)

    if telemetry_payload:
        telemetry_result = client.publish(
            f"ics/telemetry/{payload.device_id}",
            json.dumps(telemetry_payload),
            qos=1,
        )
        telemetry_result.wait_for_publish(timeout=2.0)

    time.sleep(0.1)
    client.loop_stop()
    client.disconnect()

    return {
        "status": "injected",
        "device_id": payload.device_id,
        "attack_type": payload.attack_type,
    }
