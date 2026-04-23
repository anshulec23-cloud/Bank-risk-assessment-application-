"""
Simulates 3 ICS devices publishing telemetry over MQTT.
Attack injection is triggered by sending SIGINT or via HTTP endpoint.

Usage:
    python -m mqtt.simulator              # normal mode
    python -m mqtt.simulator --attack DoS # inject attack on device-01
"""
import argparse
import json
import random
import time
import threading
import numpy as np
import paho.mqtt.client as mqtt
from core.config import settings

DEVICES = [
    {"id": "device-01", "type": "power_plant",     "location": "Zone-A"},
    {"id": "device-02", "type": "water_treatment",  "location": "Zone-B"},
    {"id": "device-03", "type": "factory",          "location": "Zone-C"},
]

NORMAL = {
    "temperature": (65.0, 3.0),
    "pressure":    (4.5,  0.2),
    "flow_rate":   (120.0, 8.0),
    "voltage":     (230.0, 4.0),
}

ATTACK_PROFILES = {
    "DoS":            {"temperature": (92.0, 6.0), "pressure": (7.8, 0.4), "flow_rate": (45.0, 15.0), "voltage": (230.0, 4.0)},
    "Spoofing":       {"temperature": (65.0, 0.05),"pressure": (4.5, 0.01),"flow_rate": (120.0, 0.1), "voltage": (230.0, 0.1)},
    "Replay":         {"temperature": (65.0, 3.0), "pressure": (4.5, 0.2), "flow_rate": (120.0, 8.0), "voltage": (193.0, 2.0)},
    "PhysicalTamper": {"temperature": (115.0,12.0),"pressure": (9.2, 0.8),"flow_rate":  (8.0,  4.0), "voltage": (178.0, 8.0)},
}

# Global attack injection state
_attack_state: dict[str, str | None] = {d["id"]: None for d in DEVICES}
_lock = threading.Lock()


def inject_attack(device_id: str, attack_type: str | None):
    with _lock:
        _attack_state[device_id] = attack_type


def _handle_command(msg_payload: bytes):
    try:
        command = json.loads(msg_payload.decode())
    except Exception as exc:
        print(f"[SIMULATOR] Bad command payload: {exc}")
        return

    action = command.get("action")
    device_id = command.get("device_id")

    if action == "INJECT_ATTACK" and device_id in _attack_state:
        attack_type = command.get("attack_type")
        inject_attack(device_id, attack_type)
        print(f"[SIMULATOR] Injecting {attack_type} on {device_id}")
    elif action == "ISOLATE" and device_id in _attack_state:
        print(f"[SIMULATOR] Received isolate command for {device_id}")


def _sample(profile: dict) -> dict:
    return {k: round(float(np.random.normal(*v)), 3) for k, v in profile.items()}


def _build_payload(device: dict) -> dict:
    with _lock:
        attack = _attack_state.get(device["id"])

    profile = ATTACK_PROFILES.get(attack, NORMAL) if attack else NORMAL
    readings = _sample(profile)

    return {
        "device_id":   device["id"],
        "device_type": device["type"],
        "location":    device["location"],
        "attack_type": attack or "None",
        **readings,
        "timestamp":   time.time(),
    }


def run_simulator(interval: float = 2.0, initial_attack: str | None = None, target_device: str = "device-01"):
    if initial_attack:
        inject_attack(target_device, initial_attack)
        print(f"[SIMULATOR] Injecting {initial_attack} on {target_device}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = lambda _client, _userdata, msg: _handle_command(msg.payload)
    client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
    client.loop_start()
    client.subscribe(f"{settings.MQTT_TOPIC_COMMANDS}/#", qos=1)

    print(f"[SIMULATOR] Publishing to {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
    try:
        while True:
            for device in DEVICES:
                payload = _build_payload(device)
                topic = f"ics/telemetry/{device['id']}"
                client.publish(topic, json.dumps(payload), qos=1)
                print(f"[{device['id']}] {payload}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("[SIMULATOR] Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attack", type=str, default=None, choices=list(ATTACK_PROFILES.keys()))
    parser.add_argument("--device", type=str, default="device-01")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()
    run_simulator(interval=args.interval, initial_attack=args.attack, target_device=args.device)
