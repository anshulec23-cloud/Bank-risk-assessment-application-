"""
Enterprise error handling and exception management.

Implements:
- Custom exception hierarchy for domain-specific errors
- Standardized error responses
- Exception telemetry and logging
- Graceful degradation patterns
"""

import logging
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    
    # Domain-specific errors
    MQTT_ERROR = "MQTT_ERROR"
    ML_MODEL_ERROR = "ML_MODEL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    LLM_ERROR = "LLM_ERROR"
    PIPELINE_ERROR = "PIPELINE_ERROR"


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error_code: str
    message: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid device ID format",
                "detail": "Device ID must be alphanumeric",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-04-15T10:30:00Z",
            }
        }


class CyberRiskException(Exception):
    """Base exception for CyberRisk platform."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        detail: Optional[str] = None,
        status_code: int = 500,
        cause: Optional[Exception] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.status_code = status_code
        self.cause = cause
        super().__init__(message)


class ValidationError(CyberRiskException):
    """Raised when input validation fails."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            detail=detail,
            status_code=422,
        )


class NotFoundError(CyberRiskException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=f"{resource} not found",
            detail=f"No {resource} with ID: {identifier}",
            status_code=404,
        )


class MQTTError(CyberRiskException):
    """Raised when MQTT operations fail."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.MQTT_ERROR,
            message=message,
            detail=str(cause) if cause else None,
            status_code=500,
            cause=cause,
        )


class MLModelError(CyberRiskException):
    """Raised when ML model operations fail."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.ML_MODEL_ERROR,
            message=message,
            detail=str(cause) if cause else None,
            status_code=500,
            cause=cause,
        )


class DatabaseError(CyberRiskException):
    """Raised when database operations fail."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            detail=str(cause) if cause else None,
            status_code=500,
            cause=cause,
        )


class LLMError(CyberRiskException):
    """Raised when LLM operations fail."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.LLM_ERROR,
            message=message,
            detail=str(cause) if cause else None,
            status_code=503,
            cause=cause,
        )


class PipelineError(CyberRiskException):
    """Raised when pipeline execution fails."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(
            error_code=ErrorCode.PIPELINE_ERROR,
            message=message,
            detail=str(cause) if cause else None,
            status_code=500,
            cause=cause,
        )


def log_exception(exc: Exception, context: Optional[dict] = None) -> None:
    """Log exception with context for observability."""
    extra = context or {}
    if isinstance(exc, CyberRiskException):
        logger.error(
            f"{exc.error_code.value}: {exc.message}",
            extra={"detail": exc.detail, **extra},
            exc_info=exc.cause or exc,
        )
    else:
        logger.error(f"Unexpected error: {str(exc)}", extra=extra, exc_info=exc)
