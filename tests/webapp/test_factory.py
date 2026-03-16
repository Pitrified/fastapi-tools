"""Tests for the application factory."""

from httpx import ASGITransport
from httpx import AsyncClient
import pytest

from fastapi_tools.config.webapp_config import GoogleOAuthConfig
from fastapi_tools.config.webapp_config import SessionConfig
from fastapi_tools.config.webapp_config import WebappConfig
from fastapi_tools.factory import create_app


def _make_config(*, debug: bool = True) -> WebappConfig:
    return WebappConfig(
        debug=debug,
        session=SessionConfig(secret_key="test-secret-key-for-testing"),
        google_oauth=GoogleOAuthConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
        ),
    )


def _make_client(app) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """GET /health returns 200."""
    app = create_app(_make_config())
    async with _make_client(app) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_live_endpoint() -> None:
    """GET /health/live returns 200."""
    app = create_app(_make_config())
    async with _make_client(app) as client:
        resp = await client.get("/health/live")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_status_unauthenticated() -> None:
    """GET /auth/status without session returns unauthenticated."""
    app = create_app(_make_config())
    async with _make_client(app) as client:
        resp = await client.get("/auth/status")
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is False


@pytest.mark.asyncio
async def test_auth_me_requires_login() -> None:
    """GET /auth/me without session returns 401."""
    app = create_app(_make_config())
    async with _make_client(app) as client:
        resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_docs_available_in_debug() -> None:
    """Self-hosted /docs should be available in debug mode."""
    app = create_app(_make_config())
    async with _make_client(app) as client:
        resp = await client.get("/docs")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_security_headers_present() -> None:
    """Security headers should be present on responses."""
    app = create_app(_make_config())
    async with _make_client(app) as client:
        resp = await client.get("/health")
    assert "x-request-id" in resp.headers
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"


@pytest.mark.asyncio
async def test_google_login_redirect() -> None:
    """GET /auth/google/login should redirect to Google."""
    config = _make_config()
    app = create_app(config)

    # Manually initialise auth state (lifespan isn't triggered by httpx)
    from fastapi_tools.auth.google import GoogleAuthService
    from fastapi_tools.auth.google import SessionStore

    ss = SessionStore()
    app.state.session_store = ss
    app.state.auth_service = GoogleAuthService(
        oauth_config=config.google_oauth,
        session_config=config.session,
        session_store=ss,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as client:
        resp = await client.get("/auth/google/login")
    assert resp.status_code == 302
    assert "accounts.google.com" in resp.headers["location"]
