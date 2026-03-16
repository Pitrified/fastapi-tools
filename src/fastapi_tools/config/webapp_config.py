"""Webapp configuration models.

These Pydantic models define the structure of webapp settings.
Actual values are provided by WebappParams in the consuming project.
"""

from typing import Literal

from pydantic import Field

from fastapi_tools.data_models.basemodel_kwargs import BaseModelKwargs


class CORSConfig(BaseModelKwargs):
    """CORS middleware configuration."""

    allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="List of allowed origins",
    )
    allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="List of allowed HTTP methods",
    )
    allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="List of allowed headers",
    )
    allow_credentials: bool = Field(
        default=True,
        description="Whether to allow credentials (cookies, auth headers)",
    )


class SessionConfig(BaseModelKwargs):
    """Session management configuration."""

    secret_key: str = Field(
        description="Secret key for session signing (64-char hex recommended)",
    )
    session_cookie_name: str = Field(
        default="session",
        description="Name of the session cookie",
    )
    max_age: int = Field(
        default=86400,  # 24 hours
        description="Session max age in seconds",
    )
    same_site: Literal["lax", "strict", "none"] = Field(
        default="lax",
        description="SameSite cookie attribute",
    )
    https_only: bool = Field(
        default=False,
        description="Whether to require HTTPS for cookies (enable in prod)",
    )


class RateLimitConfig(BaseModelKwargs):
    """Rate limiting configuration."""

    requests_per_minute: int = Field(
        default=100,
        description="Maximum requests per minute per IP",
    )
    burst_size: int = Field(
        default=10,
        description="Allowed burst size above the rate limit",
    )
    auth_requests_per_minute: int = Field(
        default=10,
        description="Maximum auth requests per minute per IP (stricter)",
    )


class GoogleOAuthConfig(BaseModelKwargs):
    """Google OAuth 2.0 configuration."""

    client_id: str = Field(
        description="Google OAuth 2.0 client ID",
    )
    client_secret: str = Field(
        default="",
        description="Google OAuth 2.0 client secret (for server-side flow)",
    )
    redirect_uri: str = Field(
        default="http://localhost:8000/auth/google/callback",
        description="OAuth callback redirect URI",
    )
    scopes: list[str] = Field(
        default_factory=lambda: [
            "openid",
            "email",
            "profile",
        ],
        description="OAuth scopes to request",
    )


class WebappConfig(BaseModelKwargs):
    """Main webapp configuration aggregating all sub-configs."""

    host: str = Field(
        default="0.0.0.0",  # noqa: S104
        description="Server bind host",
    )
    port: int = Field(
        default=8000,
        description="Server bind port",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    app_name: str = Field(
        default="FastAPI App",
        description="Application name for OpenAPI docs",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
    )
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"],
        description=(
            "Allowed Host header values for TrustedHostMiddleware. "
            "Include the public domain when running behind a reverse proxy."
        ),
    )
    public_base_url: str | None = Field(
        default=None,
        description=(
            "Explicit public base URL (e.g. https://yourdomain.com). "
            "Used to build OAuth redirect URIs behind a reverse proxy. "
            "If None, the base URL is inferred from X-Forwarded-* request headers."
        ),
    )
    cors: CORSConfig = Field(
        default_factory=CORSConfig,
        description="CORS configuration",
    )
    session: SessionConfig = Field(
        description="Session configuration",
    )
    rate_limit: RateLimitConfig = Field(
        default_factory=RateLimitConfig,
        description="Rate limiting configuration",
    )
    google_oauth: GoogleOAuthConfig = Field(
        description="Google OAuth configuration",
    )
