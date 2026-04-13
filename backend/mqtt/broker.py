"""
Async MQTT listener.
Subscribes to ics/telemetry/# and pushes each message into the LangGraph pipeline.
"""
import asyncio
import json
import threading
import paho.mqtt.client as mqtt
from core.config import settings


class MQTTListener:
    def __init__(self, pipeline_callback):
        """
        pipeline_callback: async callable(payload: dict) — called for each telemetry message.
        """
        self._callback = pipeline_callback
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(settings.MQTT_TOPIC_TELEMETRY, qos=1)
            print(f"[MQTT] Connected — subscribed to {settings.MQTT_TOPIC_TELEMETRY}")
        else:
            print(f"[MQTT] Connection failed: {reason_code}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except Exception as e:
            print(f"[MQTT] Bad payload: {e}")
            return

        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._callback(payload), self._loop)

    def start(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)

        self._thread = threading.Thread(target=self._client.loop_forever, daemon=True)
        self._thread.start()
        print("[MQTT] Listener started in background thread.")

    def stop(self):
        self._client.disconnect()
        print("[MQTT] Listener stopped.")

    def publish_isolation_command(self, device_id: str):
        """Sends isolation command to a device."""
        command = json.dumps({"action": "ISOLATE", "device_id": device_id})
        self._client.publish(f"{settings.MQTT_TOPIC_COMMANDS}/{device_id}", command, qos=2)
        print(f"[MQTT] Isolation command sent → {device_id}")
