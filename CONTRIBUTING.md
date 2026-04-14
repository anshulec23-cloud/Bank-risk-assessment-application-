# Contributing to CyberRisk Intelligence Platform

Welcome! This document outlines development practices, standards, and workflows for contributing to the CyberRisk platform.

## Table of Contents

- [Code Standards](#code-standards)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Git Workflow](#git-workflow)
- [Testing](#testing)
- [API Design](#api-design)
- [Performance Guidelines](#performance-guidelines)
- [Security Considerations](#security-considerations)

---

## Code Standards

### Python Style Guide

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with the following additions:

- **Type hints required** for all functions and public methods
- **Docstrings**: Use Google-style docstrings for modules, classes, and functions
- **Line length**: Maximum 100 characters
- **Imports**: Organize as `stdlib` → `third-party` → `local` (isort-compatible)

**Example:**

```python
"""Module docstring explaining purpose and key exports."""

from typing import Optional, List
import logging
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel, Field

from core.config import settings
from core.exceptions import ValidationError


logger = logging.getLogger(__name__)


class SensorReading(BaseModel):
    """Represents a single sensor measurement.
    
    Attributes:
        temperature: Celsius
        pressure: PSI
        timestamp: UTC datetime of measurement
    """
    temperature: float = Field(..., ge=-50, le=150)
    pressure: float = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


def validate_device_id(device_id: str) -> None:
    """Validate device ID format.
    
    Args:
        device_id: Device identifier to validate.
        
    Raises:
        ValidationError: If format is invalid.
    """
    if not device_id.startswith("device-"):
        raise ValidationError(f"Invalid device ID: {device_id}")
```

### Type Hints

- Always specify return types
- Use `Optional[T]` for nullable values (not `T | None`)
- Use `Union` for multiple types
- Avoid `Any` unless absolutely necessary

```python
# Good
def process_telemetry(data: dict[str, float]) -> List[Incident]:
    ...

# Avoid
def process_telemetry(data: Any) -> Any:
    ...
```

---

## Project Structure

### Backend Architecture

```
backend/
├── core/
│   ├── config.py          # Configuration management
│   ├── logging.py         # Structured logging
│   ├── exceptions.py      # Exception hierarchy
│   └── schemas.py         # OpenAPI/Pydantic schemas
├── db/
│   ├── models.py          # SQLAlchemy ORM models
│   ├── database.py        # Session management
│   └── migrations/        # Alembic migrations
├── ml/
│   ├── model.py           # Random Forest model
│   ├── data_gen.py        # Synthetic data generator
│   └── artifacts/         # Trained models (gitignored)
├── mqtt/
│   ├── broker.py          # MQTT listener
│   └── simulator.py       # ICS device simulator
├── agents/
│   ├── detector.py        # Agent 1: Anomaly detection
│   ├── classifier.py      # Agent 2: Attack classification
│   ├── isolator.py        # Agent 3: Isolation decision
│   ├── risk_quantifier.py # Agent 4: Financial risk
│   └── reporter.py        # Agent 5: Report generation
├── pipeline/
│   ├── state.py           # LangGraph state schema
│   └── graph.py           # DAG definition
├── api/
│   ├── main.py            # FastAPI application
│   └── routes/            # API endpoints
│       ├── devices.py     # Device management
│       ├── incidents.py   # Incident queries
│       ├── reports.py     # Report retrieval
│       ├── telemetry.py   # Telemetry data
│       └── demo.py        # Demo endpoints
├── requirements.txt       # Dependencies
└── Dockerfile
```

### Layer Responsibilities

- **Core**: Configuration, logging, errors, schemas
- **DB**: Data persistence, models, migrations
- **ML**: Model training, inference, data generation
- **MQTT**: Device communication, protocol handling
- **Agents**: Business logic, decision making
- **Pipeline**: Workflow orchestration
- **API**: HTTP interface, serialization, validation

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node 20+
- Docker & Docker Compose
- Git

### Local Environment

```bash
# Clone repository
git clone https://github.com/anshulec23-cloud/Bank-risk-assessment-application-.git
cd cyberrisk-platform

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools

# Environment configuration
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -m scripts.seed_devices

# Train ML model (one-time)
python -m ml.model

# Start API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173

# MQTT Broker
# Ensure Mosquitto is running on localhost:1883
# Or use Docker: docker run -it -p 1883:1883 eclipse-mosquitto

# Run simulator
python -m mqtt.simulator
```

---

## Git Workflow

### Branch Naming

- `feature/description` — New features
- `bugfix/description` — Bug fixes
- `docs/description` — Documentation
- `refactor/description` — Code improvements

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`  
**Scope:** `agents`, `api`, `db`, `ml`, `mqtt`, `pipeline`, `ui`

**Examples:**

```
feat(agents): add confidence score filtering to classifier
fix(api): handle null correlation_id in error responses
docs: add deployment guide for production
refactor(pipeline): extract state validation to separate module
test(ml): add unit tests for anomaly threshold validation
```

### Pull Request Process

1. Create feature branch from `main`
2. Make atomic, well-documented commits
3. Write descriptive PR title and description
4. Link related issues (`Closes #123`)
5. Request review from 2+ maintainers
6. Address feedback with additional commits
7. Squash commits if requested
8. Merge using "Squash and merge" for clean history

**PR Template:**

```markdown
## Description
Brief explanation of changes and motivation.

## Changes
- Change 1
- Change 2

## Testing
How to verify these changes work correctly.

## Checklist
- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Tests added/updated
- [ ] No breaking changes to API
```

---

## Testing

### Test Structure

```
tests/
├── unit/
│   ├── test_agents/
│   ├── test_api/
│   └── test_ml/
├── integration/
│   ├── test_pipeline.py
│   └── test_mqtt.py
└── fixtures.py
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test module
pytest tests/unit/test_agents/test_detector.py

# Run with verbose output
pytest -v

# Watch mode (requires pytest-watch)
ptw
```

### Test Patterns

**Unit Test Example:**

```python
"""tests/unit/test_agents/test_detector.py"""
import pytest
from backend.agents.detector import detect_anomaly


@pytest.fixture
def normal_telemetry():
    return {
        "temperature": 75.0,
        "pressure": 250.0,
        "flow_rate": 120.0,
        "voltage": 230.0,
    }


def test_detect_anomaly_normal_telemetry(normal_telemetry):
    """Normal telemetry should not trigger anomaly detection."""
    result = detect_anomaly(normal_telemetry)
    assert result["is_anomaly"] is False
    assert result["anomaly_score"] < 0.65


def test_detect_anomaly_temperature_spike(normal_telemetry):
    """Temperature spike should trigger anomaly."""
    anomalous = normal_telemetry.copy()
    anomalous["temperature"] = 150.0  # Extreme spike
    
    result = detect_anomaly(anomalous)
    assert result["is_anomaly"] is True
    assert result["anomaly_score"] > 0.7
```

### Coverage Requirements

- Unit tests: Minimum 80% coverage
- Integration tests: Critical paths covered
- Manual testing: Before each release

---

## API Design

### Endpoint Standards

- **RESTful principles**: Use correct HTTP methods
- **Versioning**: Include in URL prefix `/api/v1/`
- **Pagination**: Use `limit` and `offset` query params
- **Filtering**: Support common filters (e.g., `severity`, `status`)
- **Sorting**: Default to most recent first

### Request/Response Format

```python
# Good: Pagination + filtering
GET /api/v1/incidents?severity=CRITICAL&status=unresolved&limit=50&offset=0

# Response structure
{
    "data": [...],
    "pagination": {
        "total": 150,
        "limit": 50,
        "offset": 0
    },
    "timestamp": "2025-04-15T10:30:00Z"
}
```

### Error Responses

All errors follow standardized format:

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Invalid incident ID format",
    "detail": "Expected 'INC-YYYY-NNN' format",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-04-15T10:30:00Z"
}
```

---

## Performance Guidelines

### Database Optimization

- Add indexes on frequently filtered columns
- Use `select()` with specific columns (avoid `SELECT *`)
- Batch operations when possible
- Monitor query execution time

```python
# Good: Explicit columns + index
db.query(Incident.id, Incident.severity).filter(
    Incident.created_at > cutoff_time
).all()

# Avoid: Full table scan
db.query(Incident).filter(Incident.custom_field == value).all()
```

### API Response Times

- Telemetry ingestion: < 100ms
- API endpoints: < 500ms (99th percentile)
- Dashboard updates: < 1s

### Memory Usage

- Avoid loading entire datasets into memory
- Stream large responses
- Use generators for bulk operations

---

## Security Considerations

### Input Validation

- Validate all external inputs
- Use Pydantic models with constraints
- Reject malformed requests early

```python
# Good
class DeviceQuery(BaseModel):
    device_id: str = Field(..., regex=r"^device-\d+$")
    severity: SeverityLevel  # Enum validation
    limit: int = Field(default=100, le=1000)

# Avoid
device_id = request.query_params.get("device_id")  # Unchecked
```

### Secrets Management

- Never commit `.env` files
- Use environment variables for secrets
- Support external secret managers (AWS Secrets Manager, Vault)
- Rotate credentials regularly

### CORS & Authentication

- Restrict CORS origins in production
- Implement API key validation for sensitive endpoints
- Log all authentication failures
- Rate limit to prevent abuse

### Logging

- Never log secrets or sensitive data
- Use structured logging with context
- Include request IDs for traceability

---

## Release Process

1. Update version in `backend/core/config.py`
2. Update `CHANGELOG.md`
3. Create release branch: `release/v1.0.0`
4. Tag commit: `git tag -a v1.0.0`
5. Create GitHub release with notes
6. Deploy to production

---

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for design questions
- Tag maintainers `@anshulec23-cloud` for urgent matters

Happy coding! 🚀
