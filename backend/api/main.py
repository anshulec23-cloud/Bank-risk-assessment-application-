"""
FastAPI application entry point with enterprise-grade patterns.

Features:
- Structured logging with correlation IDs
- Comprehensive error handling
- Lifespan event management
- CORS and security middleware
- OpenAPI documentation
- Graceful shutdown
- Health checks and readiness probes

Pipeline flow:
  MQTT Telemetry → 5-agent LangGraph → DB + WebSocket → React Dashboard
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings, Environment
from core.logging import setup_logging, set_correlation_id, get_logger
from core.exceptions import CyberRiskException, ErrorResponse, log_exception
from db.database import init_db, SessionLocal
from db import models
from ml.model import get_model
from mqtt.broker import MQTTListener
from pipeline.graph import run_pipeline
from api.routes import telemetry, incidents, devices, reports, demo

logger = get_logger(__name__)


# ── WebSocket Connection Manager ─────────────────────────────────────────────
class ConnectionManager:
    """Manages WebSocket connections with graceful error handling."""

    def __init__(self):
        self.active: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        """Accept and register a WebSocket connection."""
        await ws.accept()
        async with self._lock:
            self.active.append(ws)
        logger.info(f"WebSocket connected. Active connections: {len(self.active)}")

    async def disconnect(self, ws: WebSocket):
        """Safely disconnect a WebSocket."""
        async with self._lock:
            if ws in self.active:
                self.active.remove(ws)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients with error handling."""
        dead_connections = []
        async with self._lock:
            for ws in self.active:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to client: {e}")
                    dead_connections.append(ws)

        # Clean up dead connections
        for ws in dead_connections:
            await self.disconnect(ws)


ws_manager = ConnectionManager()
mqtt_listener: Optional[MQTTListener] = None


# ── Telemetry Handler ────────────────────────────────────────────────────────
async def handle_telemetry(payload: dict):
    """
    Process telemetry and run 5-agent pipeline.
    
    Flow:
    1. Run LangGraph pipeline with anomaly detection, classification, isolation, risk quantification
    2. Persist results to database
    3. Broadcast to WebSocket clients
    4. Log incidents with full context
    """
    correlation_id = payload.get("correlation_id", set_correlation_id())
    logger.info(f"Processing telemetry from device: {payload.get('device_id')}")

    try:
        # Run pipeline in thread pool (blocking operation)
        state = await asyncio.to_thread(run_pipeline, payload)
    except Exception as e:
        log_exception(e, {"device_id": payload.get("device_id")})
        return

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
            logger.warning(f"Device {payload['device_id']} isolated due to threat")
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
            logger.critical(
                f"Incident created: {inc.incident_id} - {inc.attack_type} (${inc.total_exposure_usd:,.0f} exposure)"
            )

        db.commit()

        # Broadcast live update to all WebSocket clients
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

    except Exception as e:
        log_exception(e, {"device_id": payload.get("device_id")})
    finally:
        db.close()


# ── Lifespan Management ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    global mqtt_listener
    
    logger.info("Starting CyberRisk Platform...")
    try:
        init_db()
        logger.info("Database initialized")
        
        get_model()  # Warm up Random Forest model
        logger.info("ML model loaded")
        
        loop = asyncio.get_event_loop()
        mqtt_listener = MQTTListener(handle_telemetry)
        mqtt_listener.start(loop)
        logger.info("MQTT listener started")
        
        logger.info("✓ All startup checks passed")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    logger.info("Shutting down CyberRisk Platform...")
    try:
        if mqtt_listener:
            mqtt_listener.stop()
        logger.info("✓ Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# ── FastAPI Application ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time ICS cyberattack detection with financial risk quantification",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# ── Middleware ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# ── Exception Handlers ───────────────────────────────────────────────────────
@app.exception_handler(CyberRiskException)
async def cyberrisk_exception_handler(request, exc: CyberRiskException):
    """Handle custom CyberRisk exceptions with structured response."""
    log_exception(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code.value,
            message=exc.message,
            detail=exc.detail,
            request_id=request.headers.get("X-Request-ID", ""),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions gracefully."""
    log_exception(exc)
    request_id = request.headers.get("X-Request-ID", "")
    logger.error(f"Unhandled exception (Request ID: {request_id})", exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            detail=str(exc) if settings.DEBUG else None,
            request_id=request_id,
        ).model_dump(),
    )


# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["Telemetry"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(demo.router, prefix="/api/demo", tags=["Demo"])


# ── Health Checks ────────────────────────────────────────────────────────────
@app.get(
    "/api/health",
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns service health status and readiness",
)
def health_check():
    """Returns application health status."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get(
    "/api/ready",
    tags=["Health"],
    summary="Readiness probe",
    description="Indicates if service is ready to accept traffic",
)
def readiness_probe():
    """Returns readiness status."""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"ready": True, "reason": "All systems operational"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "Database connection failed"},
        )


# ── WebSocket ────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry and incident updates.
    
    Broadcasts:
    - Telemetry updates with anomaly scores
    - Incident alerts with financial risk data
    - Device isolation events
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)


# ── Initialize Logging ───────────────────────────────────────────────────────
setup_logging()
logger.info(f"CyberRisk Platform initialized (Environment: {settings.ENVIRONMENT.value})")
