"""Custom exceptions and exception handlers."""
import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpsPilotError(Exception):
    """Base exception for OpsPilot."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(OpsPilotError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(OpsPilotError):
    """Validation error."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class AuthenticationError(OpsPilotError):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(OpsPilotError):
    """Authorization error."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictError(OpsPilotError):
    """Resource conflict."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class ServiceUnavailableError(OpsPilotError):
    """Service unavailable."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        logger.warning("422 validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(OperationalError)
    async def sqlalchemy_operational_handler(request: Request, exc: OperationalError):
        """DB unreachable, auth failures at connect, etc."""
        logger.warning("Database operational error on %s: %s", request.url.path, exc)
        content: dict = {"error": "Database temporarily unavailable"}
        if settings.DEBUG:
            content["detail"] = str(exc)
            content["exception_type"] = type(exc).__name__
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=content,
        )

    @app.exception_handler(OpsPilotError)
    async def opspilot_error_handler(request: Request, exc: OpsPilotError):
        """Handle OpsPilot base exception."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all uncaught exceptions."""
        logger.exception("Unhandled error on %s", request.url.path)
        content: dict = {"error": "Internal server error"}
        if settings.DEBUG:
            content["detail"] = str(exc)
            content["exception_type"] = type(exc).__name__
            content["traceback"] = traceback.format_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content,
        )
