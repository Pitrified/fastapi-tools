"""Common Pydantic schemas shared across the webapp."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status (healthy/unhealthy)")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Response timestamp")


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    status: str = Field(description="Ready status (ready/not_ready)")
    checks: dict[str, bool] = Field(
        default_factory=dict,
        description="Individual component check results",
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(description="Error message")
    error_code: str | None = Field(
        default=None,
        description="Application error code",
    )
    request_id: str | None = Field(
        default=None,
        description="Request ID for tracking",
    )


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(description="Response message")


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")

    @classmethod
    def calculate_pages(cls, total: int, page_size: int) -> int:
        """Calculate total number of pages."""
        return (total + page_size - 1) // page_size if total > 0 else 0
