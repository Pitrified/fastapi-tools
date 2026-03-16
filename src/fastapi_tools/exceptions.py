"""Custom HTTP exceptions for the webapp."""

from fastapi import HTTPException
from fastapi import status


class NotAuthenticatedException(HTTPException):
    """Raised when a request requires authentication but none was provided."""

    def __init__(self, detail: str = "Not authenticated") -> None:  # noqa: D107
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class NotAuthorizedException(HTTPException):
    """Raised when the authenticated user lacks required permissions."""

    def __init__(self, detail: str = "Not authorized") -> None:  # noqa: D107
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class RateLimitExceededException(HTTPException):
    """Raised when a client exceeds the configured rate limit."""

    def __init__(  # noqa: D107
        self,
        detail: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        headers = {}
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers or None,
        )


class ValidationException(HTTPException):
    """Raised for request validation errors."""

    def __init__(  # noqa: D107
        self,
        detail: str = "Validation error",
        errors: list[dict] | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": detail, "errors": errors or []},
        )


class ServiceUnavailableException(HTTPException):
    """Raised when a downstream service is unavailable."""

    def __init__(self, detail: str = "Service unavailable") -> None:  # noqa: D107
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
