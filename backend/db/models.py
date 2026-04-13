from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from db.database import Base


class Device(Base):
    __tablename__ = "devices"

    id          = Column(Integer, primary_key=True, index=True)
    device_id   = Column(String(64), unique=True, index=True, nullable=False)
    device_type = Column(String(64), default="factory")   # power_plant | water_treatment | factory | oil_refinery
    location    = Column(String(128), default="Zone-A")
    is_isolated = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id            = Column(Integer, primary_key=True, index=True)
    device_id     = Column(String(64), index=True, nullable=False)
    temperature   = Column(Float, nullable=False)
    pressure      = Column(Float, nullable=False)
    flow_rate     = Column(Float, nullable=False)
    voltage       = Column(Float, nullable=False)
    anomaly_score = Column(Float, default=0.0)
    is_anomaly    = Column(Boolean, default=False)
    received_at   = Column(DateTime(timezone=True), server_default=func.now())


class Incident(Base):
    __tablename__ = "incidents"

    id              = Column(Integer, primary_key=True, index=True)
    incident_id     = Column(String(64), unique=True, index=True, nullable=False)
    device_id       = Column(String(64), index=True, nullable=False)
    attack_type     = Column(String(64), nullable=False)   # DoS | Spoofing | Replay | MitM | PhysicalTamper | Unknown
    severity        = Column(String(16), nullable=False)   # low | medium | high | critical
    confidence      = Column(Float, default=0.0)
    is_isolated     = Column(Boolean, default=False)
    isolation_time  = Column(DateTime(timezone=True), nullable=True)

    # Financial risk
    downtime_cost_usd     = Column(Float, default=0.0)
    sla_penalty_usd       = Column(Float, default=0.0)
    regulatory_fine_usd   = Column(Float, default=0.0)
    total_exposure_usd    = Column(Float, default=0.0)
    credit_risk_flag      = Column(String(16), default="NORMAL")  # NORMAL | ELEVATED | HIGH | CRITICAL

    # Reports
    nist_report     = Column(Text, nullable=True)
    credit_brief    = Column(Text, nullable=True)

    status          = Column(String(16), default="OPEN")   # OPEN | CONTAINED | RESOLVED
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at     = Column(DateTime(timezone=True), nullable=True)
