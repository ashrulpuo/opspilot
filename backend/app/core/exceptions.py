"""Custom exceptions and exception handlers."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


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
        # In production, log this error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )
