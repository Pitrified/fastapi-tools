"""Custom middleware for the webapp."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
import uuid

from loguru import logger as lg
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import Request
    from fastapi import Response
    from starlette.types import ASGIApp

    from fastapi_tools.config import WebappConfig


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add X-Request-ID header to request and response."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related HTTP headers to every response."""

    _DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")

    def __init__(self, app: ASGIApp, *, is_production: bool = False) -> None:  # noqa: D107
        super().__init__(app)
        self.is_production = is_production
        self.strict_csp = (
            "default-src 'self'"
            "; script-src 'self'"
            "; style-src 'self' 'unsafe-inline'"
            "; img-src 'self' data: https://lh3.googleusercontent.com"
            "; font-src 'self'"
            "; connect-src 'self'"
            "; frame-ancestors 'none'"
            "; base-uri 'self'"
            "; form-action 'self'"
            "; object-src 'none'"
            "; worker-src 'self'"
            "; manifest-src 'self'"
        )
        self.docs_csp = (
            "default-src 'self'"
            "; script-src 'self' 'unsafe-inline'"
            "; style-src 'self' 'unsafe-inline'"
            "; img-src 'self' data:"
            "; font-src 'self'"
            "; connect-src 'self'"
            "; frame-ancestors 'none'"
            "; base-uri 'self'"
            "; form-action 'self'"
            "; object-src 'none'"
            "; worker-src 'self'"
            "; manifest-src 'self'"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        path = request.url.path
        if any(path.startswith(prefix) for prefix in self._DOCS_PREFIXES):
            response.headers["Content-Security-Policy"] = self.docs_csp
        else:
            response.headers["Content-Security-Policy"] = self.strict_csp

        if self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and their response status/duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "unknown")
        lg.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}",
        )
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        lg.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms:.2f}ms)",
        )
        return response


def setup_middleware(app: ASGIApp, config: WebappConfig) -> None:
    """Add custom middleware stack to a FastAPI application.

    Args:
        app: FastAPI application instance.
        config: Webapp configuration.
    """
    from fastapi import FastAPI  # noqa: PLC0415

    if not isinstance(app, FastAPI):
        return
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, is_production=not config.debug)
    app.add_middleware(RequestIDMiddleware)
