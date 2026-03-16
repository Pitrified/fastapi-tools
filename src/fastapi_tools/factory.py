"""FastAPI application factory.

Creates and configures a FastAPI application with standard middleware,
exception handlers, routers, and optional static/template serving.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from collections.abc import Callable
    from pathlib import Path

    from fastapi import APIRouter

    from fastapi_tools.config import WebappConfig

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from loguru import logger as lg
from starlette.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from fastapi_tools.auth.google import GoogleAuthService
from fastapi_tools.auth.google import SessionStore
from fastapi_tools.exceptions import NotAuthenticatedException
from fastapi_tools.exceptions import NotAuthorizedException
from fastapi_tools.exceptions import RateLimitExceededException
from fastapi_tools.middleware import setup_middleware
from fastapi_tools.routers.auth import router as auth_router
from fastapi_tools.routers.health import router as health_router
from fastapi_tools.schemas.common import ErrorResponse
from fastapi_tools.templating import configure_templates
from fastapi_tools.templating import make_templates


@asynccontextmanager
async def default_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Default application lifespan - initialises SessionStore and GoogleAuthService.

    Args:
        app: FastAPI application instance.

    Yields:
        None during application lifetime.
    """
    lg.info("Starting webapp...")

    session_store = SessionStore()
    app.state.session_store = session_store

    config: WebappConfig = app.state.config
    auth_service = GoogleAuthService(
        oauth_config=config.google_oauth,
        session_config=config.session,
        session_store=session_store,
    )
    app.state.auth_service = auth_service

    lg.info("Webapp started successfully")

    yield

    lg.info("Shutting down webapp...")
    lg.info("Webapp shutdown complete")


def create_app(
    config: WebappConfig,
    *,
    extra_routers: list[APIRouter] | None = None,
    static_dir: Path | str | None = None,
    templates_dir: Path | str | None = None,
    lifespan: Callable | None = None,
) -> FastAPI:
    """Create and configure a FastAPI application.

    Args:
        config: Webapp configuration.
        extra_routers: Additional routers to include (project-specific).
        static_dir: Path to static files directory. If None, /static not mounted.
        templates_dir: Path to templates directory. If None, templating not configured.
        lifespan: Custom lifespan context manager. If None, a default is used
                  that initialises SessionStore and GoogleAuthService only.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        description=(
            "A FastAPI web application with Google OAuth authentication. "
            "Built with security best practices including rate limiting, "
            "CSRF protection, and secure session management."
        ),
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json" if config.debug else None,
        lifespan=lifespan or default_lifespan,
    )

    app.state.config = config

    # Mount static assets (before routers so /static/... is resolved first)
    if static_dir is not None:
        app.mount(
            "/static",
            StaticFiles(directory=str(static_dir)),
            name="static",
        )

    # Configure Jinja2 templates
    if templates_dir is not None:
        templates = make_templates(templates_dir)
        configure_templates(templates, config)
        app.state.templates = templates

    # Self-hosted API docs (Swagger UI + ReDoc) - no CDN dependencies
    if config.debug:
        _register_docs_routes(app)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )

    # Custom middleware (RequestID, SecurityHeaders, Logging)
    setup_middleware(app, config)

    # Host header injection protection
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if config.debug else config.trusted_hosts,
    )

    # Trust proxy headers only from local reverse proxy
    app.add_middleware(
        ProxyHeadersMiddleware,
        trusted_hosts=["127.0.0.1", "::1"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Built-in routers
    app.include_router(health_router)
    app.include_router(auth_router)

    # Project-specific routers
    if extra_routers:
        for extra_router in extra_routers:
            app.include_router(extra_router)

    lg.info(f"Created FastAPI app: {config.app_name} v{config.app_version}")

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(NotAuthenticatedException)
    async def not_authenticated_handler(
        request: Request,
        exc: NotAuthenticatedException,
    ) -> JSONResponse | RedirectResponse:
        """Handle authentication errors.

        Browser requests are redirected to the landing page.
        API requests receive a JSON 401 response.
        """
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse(url="/", status_code=302)

        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                error_code="NOT_AUTHENTICATED",
                request_id=request_id,
            ).model_dump(),
            headers=exc.headers,
        )

    @app.exception_handler(NotAuthorizedException)
    async def not_authorized_handler(
        request: Request,
        exc: NotAuthorizedException,
    ) -> JSONResponse:
        """Handle authorization errors."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                error_code="NOT_AUTHORIZED",
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(RateLimitExceededException)
    async def rate_limit_handler(
        request: Request,
        exc: RateLimitExceededException,
    ) -> JSONResponse:
        """Handle rate limit errors."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.detail,
                error_code="RATE_LIMIT_EXCEEDED",
                request_id=request_id,
            ).model_dump(),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected errors."""
        request_id = getattr(request.state, "request_id", None)
        lg.exception(f"Unhandled exception: {exc}")

        config: WebappConfig = request.app.state.config
        detail = str(exc) if config.debug else "Internal server error"

        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=detail,
                error_code="INTERNAL_ERROR",
                request_id=request_id,
            ).model_dump(),
        )


def _register_docs_routes(app: FastAPI) -> None:
    """Register self-hosted Swagger UI and ReDoc routes.

    These serve locally-bundled JS/CSS from ``/static/swagger/`` so no
    external CDN is referenced, keeping CSP strict.

    Args:
        app: FastAPI application instance.
    """

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html() -> HTMLResponse:
        """Serve Swagger UI from local static assets."""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_js_url="/static/swagger/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger/swagger-ui.css",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        )

    @app.get(
        app.swagger_ui_oauth2_redirect_url or "/docs/oauth2-redirect",
        include_in_schema=False,
    )
    async def swagger_ui_redirect() -> HTMLResponse:
        """Serve the OAuth2 redirect page for Swagger UI."""
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html() -> HTMLResponse:
        """Serve ReDoc from local static assets."""
        return get_redoc_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} - ReDoc",
            redoc_js_url="/static/swagger/redoc.standalone.js",
        )
