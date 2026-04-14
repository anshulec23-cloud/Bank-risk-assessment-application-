"""
Test configuration and shared fixtures for the CyberRisk platform test suite.

This module provides:
- Pytest configuration
- Database fixtures for testing
- Mock MQTT fixtures
- Sample telemetry data generators
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import tempfile
import os

from backend.db.models import Base
from backend.db.database import SessionLocal
from backend.core.config import Settings, Environment


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test-specific configuration."""
    return Settings(
        ENVIRONMENT=Environment.DEV,
        DATABASE_URL="sqlite:///:memory:",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
    )


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a fresh test database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture
def sample_telemetry_normal() -> dict:
    """Generate normal telemetry reading."""
    return {
        "device_id": "device-01",
        "device_type": "SCADA",
        "location": "Plant A - Zone 1",
        "temperature": 75.0,
        "pressure": 250.0,
        "flow_rate": 120.0,
        "voltage": 230.0,
    }


@pytest.fixture
def sample_telemetry_dos_attack() -> dict:
    """Generate telemetry with DoS attack signature."""
    return {
        "device_id": "device-02",
        "device_type": "PLC",
        "location": "Plant A - Zone 2",
        "temperature": 120.0,  # Spike
        "pressure": 380.0,     # Surge
        "flow_rate": 5.0,      # Drop
        "voltage": 230.0,
    }


@pytest.fixture
def sample_telemetry_physical_tamper() -> dict:
    """Generate telemetry with physical tamper signature."""
    return {
        "device_id": "device-03",
        "device_type": "RTU",
        "location": "Plant B - Zone 1",
        "temperature": 155.0,  # Extreme
        "pressure": 400.0,     # Extreme
        "flow_rate": 1.0,      # Near zero
        "voltage": 230.0,
    }


@pytest.fixture
def sample_incident_data() -> dict:
    """Generate sample incident record."""
    return {
        "incident_id": "INC-2025-001",
        "device_id": "device-01",
        "attack_type": "DoS",
        "severity": "CRITICAL",
        "confidence": 0.94,
        "is_isolated": True,
        "downtime_cost_usd": 1200000,
        "sla_penalty_usd": 180000,
        "regulatory_fine_usd": 5000000,
        "total_exposure_usd": 6380000,
        "credit_risk_flag": "CRITICAL",
    }


@pytest.fixture
def mock_mqtt_payload() -> dict:
    """Generate mock MQTT telemetry payload."""
    return {
        "device_id": "device-01",
        "temperature": 78.5,
        "pressure": 255.0,
        "flow_rate": 118.0,
        "voltage": 229.5,
        "timestamp": "2025-04-15T10:30:00Z",
    }


# pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
