"""
OpenAPI/Swagger schema definitions and API documentation models.

Implements comprehensive schema for all API endpoints with examples and validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class DeviceStatus(str, Enum):
    """Device operational status."""
    OPERATIONAL = "operational"
    ANOMALOUS = "anomalous"
    ISOLATED = "isolated"
    OFFLINE = "offline"


class SeverityLevel(str, Enum):
    """Attack severity levels (CVSS-aligned)."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CreditRiskFlag(str, Enum):
    """Financial exposure risk flags."""
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ── Device Schemas ──────────────────────────────────────────────────────────

class SensorReading(BaseModel):
    """Real-time sensor measurement."""
    temperature: float = Field(..., description="Temperature in Celsius")
    pressure: float = Field(..., description="Pressure in PSI")
    flow_rate: float = Field(..., description="Flow rate in L/min")
    voltage: float = Field(..., description="Voltage in Volts")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "temperature": 85.5,
            "pressure": 250.0,
            "flow_rate": 120.5,
            "voltage": 230.0,
            "timestamp": "2025-04-15T10:30:00Z"
        }
    })


class DeviceInfo(BaseModel):
    """Device information and current state."""
    device_id: str = Field(..., description="Unique device identifier")
    device_type: str = Field(..., description="Type of industrial device")
    location: str = Field(..., description="Physical location")
    status: DeviceStatus = Field(default=DeviceStatus.OPERATIONAL)
    is_isolated: bool = Field(default=False, description="Network isolation status")
    last_telemetry: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "device_id": "device-01",
            "device_type": "SCADA",
            "location": "Plant A - Zone 1",
            "status": "operational",
            "is_isolated": False,
            "last_telemetry": "2025-04-15T10:30:00Z",
            "created_at": "2025-04-01T00:00:00Z",
            "updated_at": "2025-04-15T10:30:00Z"
        }
    })


class DeviceListResponse(BaseModel):
    """Paginated device list response."""
    devices: List[DeviceInfo]
    total: int = Field(..., description="Total number of devices")
    limit: int = Field(default=100)
    offset: int = Field(default=0)


# ── Incident Schemas ────────────────────────────────────────────────────────

class FinancialRisk(BaseModel):
    """Financial exposure breakdown."""
    downtime_cost_usd: float = Field(..., description="Estimated downtime cost")
    sla_penalty_usd: float = Field(..., description="SLA violation penalty")
    regulatory_fine_usd: float = Field(..., description="Regulatory fine (NERC CIP)")
    total_exposure_usd: float = Field(..., description="Total financial exposure")
    credit_risk_flag: CreditRiskFlag = Field(..., description="Credit risk assessment")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "downtime_cost_usd": 1200000,
            "sla_penalty_usd": 180000,
            "regulatory_fine_usd": 5000000,
            "total_exposure_usd": 6380000,
            "credit_risk_flag": "CRITICAL"
        }
    })


class IncidentInfo(BaseModel):
    """Security incident record."""
    incident_id: str = Field(..., description="Unique incident identifier")
    device_id: str
    attack_type: str = Field(..., description="Detected attack type")
    severity: SeverityLevel
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    is_resolved: bool = Field(default=False)
    financial_risk: FinancialRisk
    anomaly_score: float = Field(..., description="ML anomaly score")
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "incident_id": "INC-2025-001",
            "device_id": "device-01",
            "attack_type": "DoS",
            "severity": "CRITICAL",
            "confidence": 0.94,
            "is_resolved": False,
            "financial_risk": {
                "downtime_cost_usd": 1200000,
                "sla_penalty_usd": 180000,
                "regulatory_fine_usd": 5000000,
                "total_exposure_usd": 6380000,
                "credit_risk_flag": "CRITICAL"
            },
            "anomaly_score": 0.87,
            "created_at": "2025-04-15T10:30:00Z",
            "resolved_at": None
        }
    })


class IncidentListResponse(BaseModel):
    """Paginated incident list with filtering support."""
    incidents: List[IncidentInfo]
    total: int
    unresolved_count: int
    critical_count: int
    limit: int = 100
    offset: int = 0


class IncidentSummary(BaseModel):
    """High-level incident statistics."""
    total_incidents: int
    unresolved_incidents: int
    critical_incidents: int
    total_financial_exposure_usd: float
    avg_severity: str
    incidents_last_24h: int
    incidents_last_7d: int


# ── Telemetry Schemas ───────────────────────────────────────────────────────

class TelemetryEvent(BaseModel):
    """Single telemetry data point."""
    device_id: str
    sensors: SensorReading
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    is_anomaly: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "device_id": "device-01",
            "sensors": {
                "temperature": 85.5,
                "pressure": 250.0,
                "flow_rate": 120.5,
                "voltage": 230.0,
                "timestamp": "2025-04-15T10:30:00Z"
            },
            "anomaly_score": 0.23,
            "is_anomaly": False,
            "timestamp": "2025-04-15T10:30:00Z"
        }
    })


class TelemetryStats(BaseModel):
    """Aggregated telemetry statistics."""
    total_events: int
    anomalies_detected: int
    anomaly_rate_percent: float
    avg_anomaly_score: float
    devices_with_anomalies: List[str]
    last_update: datetime


# ── Report Schemas ──────────────────────────────────────────────────────────

class NISTReport(BaseModel):
    """NIST SP 800-61 incident report."""
    incident_id: str
    report_type: str = Field(default="NIST SP 800-61 Computer Security Incident Response Guide")
    detection_time: datetime
    containment_time: Optional[datetime]
    eradication_time: Optional[datetime]
    recovery_time: Optional[datetime]
    attack_description: str
    affected_systems: List[str]
    recommended_actions: List[str]
    evidence_preserved: bool

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "incident_id": "INC-2025-001",
            "report_type": "NIST SP 800-61 Computer Security Incident Response Guide",
            "detection_time": "2025-04-15T10:30:00Z",
            "containment_time": "2025-04-15T10:45:00Z",
            "eradication_time": None,
            "recovery_time": None,
            "attack_description": "Denial of Service attack detected via temperature spike and pressure surge",
            "affected_systems": ["device-01", "device-02"],
            "recommended_actions": [
                "Isolate affected devices from network",
                "Verify system integrity",
                "Implement traffic filtering"
            ],
            "evidence_preserved": True
        }
    })


class CreditRiskBrief(BaseModel):
    """Financial institution credit risk assessment."""
    incident_id: str
    borrower_entity: str
    incident_severity: SeverityLevel
    financial_exposure: FinancialRisk
    credit_impact_score: float = Field(..., ge=0.0, le=100.0)
    recommendation: str
    requires_disclosure: bool

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "incident_id": "INC-2025-001",
            "borrower_entity": "Manufacturing Corp LLC",
            "incident_severity": "CRITICAL",
            "financial_exposure": {
                "downtime_cost_usd": 1200000,
                "sla_penalty_usd": 180000,
                "regulatory_fine_usd": 5000000,
                "total_exposure_usd": 6380000,
                "credit_risk_flag": "CRITICAL"
            },
            "credit_impact_score": 85.5,
            "recommendation": "Reduce credit limit; increase monitoring frequency",
            "requires_disclosure": True
        }
    })
