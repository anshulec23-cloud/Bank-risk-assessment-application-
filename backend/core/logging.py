"""
Structured logging with context propagation and observability.

Implements JSON logging for production, human-readable for development.
Integrates context variables for request tracing and correlation IDs.
"""

import logging
import json
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime

from core.config import settings, Environment, LogLevel

# Context variables for request tracing
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
user_id: ContextVar[str] = ContextVar("user_id", default="")
request_id: ContextVar[str] = ContextVar("request_id", default="")


class StructuredLogFormatter(logging.Formatter):
    """Formats logs as structured JSON for production, human-readable for dev."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record based on environment."""
        if settings.ENVIRONMENT == Environment.PRODUCTION:
            return self._format_json(record)
        return self._format_human_readable(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        """Format as JSON with context."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context variables
        if corr_id := correlation_id.get():
            log_obj["correlation_id"] = corr_id
        if req_id := request_id.get():
            log_obj["request_id"] = req_id
        if uid := user_id.get():
            log_obj["user_id"] = uid

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)

        return json.dumps(log_obj)

    def _format_human_readable(self, record: logging.LogRecord) -> str:
        """Format for human readability in development."""
        context = ""
        if corr_id := correlation_id.get():
            context += f"[{corr_id[:8]}]"
        if req_id := request_id.get():
            context += f"[{req_id[:8]}]"

        base = f"{record.levelname:8} {record.name:30} {context} {record.getMessage()}"

        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


def setup_logging() -> None:
    """Initialize structured logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.value))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredLogFormatter())
    root_logger.addHandler(console_handler)

    # Set third-party library log levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("paho").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.info(f"Logging initialized: {settings.LOG_LEVEL.value}")


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger with context support."""
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, {"correlation_id": correlation_id.get})


def set_correlation_id(correlation_id_value: Optional[str] = None) -> str:
    """Set correlation ID for request tracing."""
    cid = correlation_id_value or str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


def set_request_id(request_id_value: Optional[str] = None) -> str:
    """Set request ID for tracking."""
    rid = request_id_value or str(uuid.uuid4())
    request_id.set(rid)
    return rid
