"""Tests for custom HTTP exceptions."""

from fastapi_tools.exceptions import NotAuthenticatedException
from fastapi_tools.exceptions import NotAuthorizedException
from fastapi_tools.exceptions import RateLimitExceededException
from fastapi_tools.exceptions import ServiceUnavailableException
from fastapi_tools.exceptions import ValidationException


def test_not_authenticated_defaults() -> None:
    """Default status code and detail."""
    exc = NotAuthenticatedException()
    assert exc.status_code == 401
    assert exc.detail == "Not authenticated"
    assert exc.headers == {"WWW-Authenticate": "Bearer"}


def test_not_authenticated_custom_detail() -> None:
    """Custom detail message."""
    exc = NotAuthenticatedException(detail="Token expired")
    assert exc.detail == "Token expired"


def test_not_authorized_defaults() -> None:
    """Default 403 status."""
    exc = NotAuthorizedException()
    assert exc.status_code == 403
    assert exc.detail == "Not authorized"


def test_rate_limit_exceeded_no_retry_after() -> None:
    """429 with no Retry-After header."""
    exc = RateLimitExceededException()
    assert exc.status_code == 429


def test_rate_limit_exceeded_with_retry_after() -> None:
    """429 with Retry-After header."""
    exc = RateLimitExceededException(retry_after=30)
    assert exc.status_code == 429
    assert exc.headers is not None
    assert exc.headers["Retry-After"] == "30"


def test_validation_exception_defaults() -> None:
    """422 with default detail."""
    exc = ValidationException()
    assert exc.status_code == 422
    detail: dict[str, object] = exc.detail  # pyright: ignore[reportAssignmentType]
    assert detail["message"] == "Validation error"
    assert detail["errors"] == []


def test_validation_exception_with_errors() -> None:
    """422 with custom error list."""
    errors = [{"field": "email", "message": "invalid"}]
    exc = ValidationException(errors=errors)
    detail: dict[str, object] = exc.detail  # pyright: ignore[reportAssignmentType]
    assert detail["errors"] == errors


def test_service_unavailable_defaults() -> None:
    """503 default."""
    exc = ServiceUnavailableException()
    assert exc.status_code == 503
    assert exc.detail == "Service unavailable"
