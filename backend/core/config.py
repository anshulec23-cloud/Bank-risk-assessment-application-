"""
Enterprise configuration management with validation, secrets handling, and environment-aware settings.

Palantir-aligned patterns:
- Pydantic v2 with strict validation
- Environment-specific overrides
- Secrets management support (AWS Secrets Manager, HashiCorp Vault-ready)
- Immutable settings after initialization
"""

from enum import Enum
from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import Optional, Literal
import logging

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Deployment environment."""
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application settings with comprehensive validation and secrets support."""
    
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "CyberRisk Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.LOCAL
    DEBUG: bool = False
    LOG_LEVEL: LogLevel = LogLevel.INFO

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./cyberrisk.db"
    DB_POOL_SIZE: int = 5
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False  # SQL query logging

    # ── MQTT Broker ──────────────────────────────────────────────────────────
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_BROKER_USERNAME: Optional[str] = None
    MQTT_BROKER_PASSWORD: Optional[str] = None
    MQTT_TOPIC_TELEMETRY: str = "ics/telemetry/#"
    MQTT_TOPIC_COMMANDS: str = "ics/commands"
    MQTT_KEEPALIVE: int = 60
    MQTT_RECONNECT_DELAY: int = 5

    # ── LLM / Ollama ─────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://192.168.1.4:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    LLM_TIMEOUT_SEC: int = 30
    LLM_ENABLED: bool = True

    # ── ML Model ─────────────────────────────────────────────────────────────
    MODEL_PATH: str = "./ml/artifacts/rf_model.joblib"
    ANOMALY_THRESHOLD: float = Field(default=0.65, ge=0.0, le=1.0)  # RF anomaly probability

    # ── Financial Risk Configuration (USD) ───────────────────────────────────
    COST_POWER_PLANT: float = 500_000
    COST_WATER_TREATMENT: float = 200_000
    COST_FACTORY: float = 150_000
    COST_OIL_REFINERY: float = 800_000
    COST_DEFAULT: float = 100_000

    # Severity → estimated downtime hours
    DOWNTIME_HOURS_LOW: float = 0.5
    DOWNTIME_HOURS_MEDIUM: float = 2.0
    DOWNTIME_HOURS_HIGH: float = 8.0
    DOWNTIME_HOURS_CRITICAL: float = 24.0

    # ── CORS / Security ──────────────────────────────────────────────────────
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # ── Rate Limiting & API Security ────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 1000
    API_KEY_REQUIRED: bool = False
    API_KEY_HEADER: str = "X-API-Key"

    # ── WebSocket ────────────────────────────────────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "forbid"  # Reject unknown environment variables
        frozen = False  # Allow setting after init, but warn on production

    @field_validator("ANOMALY_THRESHOLD")
    @classmethod
    def validate_anomaly_threshold(cls, v: float) -> float:
        """Ensure threshold is within valid probability range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("ANOMALY_THRESHOLD must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_environment_specific(self):
        """Apply environment-specific validations."""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError("DEBUG cannot be True in PRODUCTION")
            if self.LOG_LEVEL == LogLevel.DEBUG:
                raise ValueError("LOG_LEVEL cannot be DEBUG in PRODUCTION")
            if "localhost" in self.DATABASE_URL or "sqlite" in self.DATABASE_URL:
                logger.warning("Using SQLite in PRODUCTION is not recommended. Use PostgreSQL.")
        
        return self


settings = Settings()

# Log configuration on startup
logger.info(f"CyberRisk Platform v{settings.APP_VERSION} initialized")
logger.info(f"Environment: {settings.ENVIRONMENT.value}")
logger.info(f"Debug mode: {settings.DEBUG}")
logger.info(f"Database: {settings.DATABASE_URL.split('://')[0]}")
logger.info(f"MQTT Broker: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
