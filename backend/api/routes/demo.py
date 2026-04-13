from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from core.config import settings

router = APIRouter()


class AttackInjectionRequest(BaseModel):
    device_id: str
    attack_type: Literal["DoS", "Spoofing", "Replay", "PhysicalTamper"]


_mqtt_client: mqtt.Client | None = None


def _get_mqtt_client() -> mqtt.Client:
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        _mqtt_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
        _mqtt_client.loop_start()
    return _mqtt_client


@router.post("/inject-attack")
def inject_attack(payload: AttackInjectionRequest):
    import json
    
    cmd_topic = "ics/commands/attack"
    command = {
        "device_id": payload.device_id,
        "attack_type": payload.attack_type,
    }
    
    client = _get_mqtt_client()
    client.publish(cmd_topic, json.dumps(command), qos=1)
    
    return {
        "status": "injected",
        "device_id": payload.device_id,
        "attack_type": payload.attack_type,
    }
