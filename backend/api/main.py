"""
FastAPI application entry point.
- Initialises DB on startup
- Loads ML model on startup
- Starts MQTT listener in background thread
- Provides WebSocket endpoint for real-time dashboard updates
"""
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import init_db, SessionLocal
from db import models
from ml.model import get_model
from mqtt.broker import MQTTListener
from pipeline.graph import run_pipeline
from api.routes import telemetry, incidents, devices, reports, demo


# ── WebSocket connection manager ─────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


ws_manager = ConnectionManager()
mqtt_listener: MQTTListener | None = None


# ── Pipeline callback — called by MQTT listener for each message ─────────────
async def handle_telemetry(payload: dict):
    """
    1. Run the 5-agent pipeline
    2. Persist results to DB
    3. Broadcast to WebSocket clients
    """
    state = await asyncio.to_thread(run_pipeline, payload)

    db = SessionLocal()
    try:
        # Upsert device
        device = db.query(models.Device).filter_by(device_id=payload["device_id"]).first()
        if not device:
            device = models.Device(
                device_id=payload["device_id"],
                device_type=payload.get("device_type", "factory"),
                location=payload.get("location", "Unknown"),
            )
            db.add(device)

        # Update isolation status
        if state["isolation"].get("should_isolate"):
            device.is_isolated = True
            if mqtt_listener:
                mqtt_listener.publish_isolation_command(payload["device_id"])

        # Persist telemetry event
        event = models.TelemetryEvent(
            device_id=payload["device_id"],
            temperature=payload["temperature"],
            pressure=payload["pressure"],
            flow_rate=payload["flow_rate"],
            voltage=payload["voltage"],
            anomaly_score=state["anomaly"].get("anomaly_score", 0.0),
            is_anomaly=state["anomaly"].get("is_anomaly", False),
        )
        db.add(event)

        # Persist incident if attack detected
        incident_data = None
        if state["anomaly"].get("is_anomaly") and state["report"].get("report_id"):
            fr = state["financial_risk"]
            inc = models.Incident(
                incident_id=state["report"]["report_id"],
                device_id=payload["device_id"],
                attack_type=state["classification"]["attack_type"],
                severity=state["classification"]["severity"],
                confidence=state["classification"]["confidence"],
                is_isolated=state["isolation"]["should_isolate"],
                downtime_cost_usd=fr["downtime_cost_usd"],
                sla_penalty_usd=fr["sla_penalty_usd"],
                regulatory_fine_usd=fr["regulatory_fine_usd"],
                total_exposure_usd=fr["total_exposure_usd"],
                credit_risk_flag=fr["credit_risk_flag"],
                nist_report=state["report"].get("nist_report"),
                credit_brief=state["report"].get("credit_brief"),
            )
            db.add(inc)
            incident_data = {
                "incident_id": inc.incident_id,
                "attack_type": inc.attack_type,
                "severity": inc.severity,
                "total_exposure_usd": inc.total_exposure_usd,
                "credit_risk_flag": inc.credit_risk_flag,
            }

        db.commit()

        # Broadcast live update
        await ws_manager.broadcast({
            "type": "telemetry_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_id": payload["device_id"],
            "telemetry": payload,
            "anomaly_score": state["anomaly"].get("anomaly_score", 0.0),
            "is_anomaly": state["anomaly"].get("is_anomaly", False),
            "classification": state["classification"],
            "isolation": state["isolation"],
            "financial_risk": state["financial_risk"],
            "incident": incident_data,
        })

    finally:
        db.close()


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_listener
    init_db()
    get_model()  # warm up RF model
    loop = asyncio.get_event_loop()
    mqtt_listener = MQTTListener(handle_telemetry)
    mqtt_listener.start(loop)
    print("[APP] Startup complete.")
    yield
    mqtt_listener.stop()
    print("[APP] Shutdown complete.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["Telemetry"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(devices.router,   prefix="/api/devices",   tags=["Devices"])
app.include_router(reports.router,   prefix="/api/reports",   tags=["Reports"])
app.include_router(demo.router,      prefix="/api/demo",      tags=["Demo"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
