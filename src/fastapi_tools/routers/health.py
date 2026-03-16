"""Health check router for monitoring endpoints."""

from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi import Request

from fastapi_tools.schemas.common import HealthResponse
from fastapi_tools.schemas.common import ReadinessResponse

if TYPE_CHECKING:
    from fastapi_tools.config import WebappConfig

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
async def health_check(request: Request) -> HealthResponse:
    """Return a basic health status."""
    config: WebappConfig = request.app.state.config
    return HealthResponse(
        status="healthy",
        version=config.app_version,
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", summary="Readiness probe")
async def readiness_check(request: Request) -> ReadinessResponse:
    """Check whether all required components are operational."""
    config: WebappConfig = request.app.state.config
    checks: dict[str, bool] = {}
    try:
        checks["config"] = bool(config)
    except (ValueError, AttributeError, KeyError):
        checks["config"] = False
    try:
        checks["google_oauth"] = bool(config.google_oauth.client_id)
    except (ValueError, AttributeError, KeyError):
        checks["google_oauth"] = False
    all_ready = all(checks.values())
    return ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        checks=checks,
    )


@router.get("/live", summary="Liveness probe")
async def liveness_check() -> dict:
    """Return a simple liveness status."""
    return {"status": "alive"}
