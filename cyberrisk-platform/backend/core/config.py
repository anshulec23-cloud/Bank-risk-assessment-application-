from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CyberRisk Intelligence Platform"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./cyberrisk.db"

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_TELEMETRY: str = "ics/telemetry/#"
    MQTT_TOPIC_COMMANDS: str = "ics/commands"

    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    DEMO_MODE: bool = False

    # ML Model
    MODEL_PATH: str = "./ml/artifacts/rf_model.joblib"
    ANOMALY_THRESHOLD: float = 0.65  # RF anomaly probability threshold

    # Financial Risk — hourly downtime cost by device type (USD)
    COST_POWER_PLANT: float = 500_000
    COST_WATER_TREATMENT: float = 200_000
    COST_FACTORY: float = 150_000
    COST_OIL_REFINERY: float = 800_000
    COST_DEFAULT: float = 100_000

    # Severity → estimated downtime hours mapping
    DOWNTIME_HOURS_LOW: float = 0.5
    DOWNTIME_HOURS_MEDIUM: float = 2.0
    DOWNTIME_HOURS_HIGH: float = 8.0
    DOWNTIME_HOURS_CRITICAL: float = 24.0

    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
