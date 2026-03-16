"""Tests for webapp configuration models."""

from fastapi_tools.config.webapp_config import CORSConfig
from fastapi_tools.config.webapp_config import GoogleOAuthConfig
from fastapi_tools.config.webapp_config import RateLimitConfig
from fastapi_tools.config.webapp_config import SessionConfig
from fastapi_tools.config.webapp_config import WebappConfig


class TestCORSConfig:
    """Tests for CORSConfig."""

    def test_defaults(self) -> None:
        """Verify sensible defaults."""
        c = CORSConfig()
        assert "http://localhost:3000" in c.allow_origins
        assert c.allow_credentials is True

    def test_custom_origins(self) -> None:
        """Custom origins override defaults."""
        c = CORSConfig(allow_origins=["https://example.com"])
        assert c.allow_origins == ["https://example.com"]


class TestSessionConfig:
    """Tests for SessionConfig."""

    def test_required_secret(self) -> None:
        """secret_key is required."""
        c = SessionConfig(secret_key="abc123")
        assert c.secret_key == "abc123"

    def test_defaults(self) -> None:
        """Default values are set."""
        c = SessionConfig(secret_key="x")
        assert c.session_cookie_name == "session"
        assert c.max_age == 86400
        assert c.same_site == "lax"
        assert c.https_only is False


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_defaults(self) -> None:
        """Default rate limit values."""
        c = RateLimitConfig()
        assert c.requests_per_minute == 100
        assert c.burst_size == 10
        assert c.auth_requests_per_minute == 10


class TestGoogleOAuthConfig:
    """Tests for GoogleOAuthConfig."""

    def test_required_client_id(self) -> None:
        """client_id is required."""
        c = GoogleOAuthConfig(client_id="cid")
        assert c.client_id == "cid"
        assert c.client_secret == ""

    def test_default_scopes(self) -> None:
        """Default scopes should include openid, email, profile."""
        c = GoogleOAuthConfig(client_id="cid")
        assert "openid" in c.scopes
        assert "email" in c.scopes
        assert "profile" in c.scopes


class TestWebappConfig:
    """Tests for WebappConfig."""

    def test_defaults(self) -> None:
        """Full config with default sub-configs."""
        c = WebappConfig(
            session=SessionConfig(secret_key="s"),
            google_oauth=GoogleOAuthConfig(client_id="c"),
        )
        assert c.host == "0.0.0.0"  # noqa: S104
        assert c.port == 8000
        assert c.debug is False
        assert c.app_name == "FastAPI App"
        assert c.trusted_hosts == ["localhost", "127.0.0.1"]
        assert c.public_base_url is None

    def test_custom_values(self) -> None:
        """Override all defaults."""
        c = WebappConfig(
            host="127.0.0.1",
            port=9000,
            debug=True,
            app_name="My App",
            app_version="2.0",
            trusted_hosts=["example.com"],
            public_base_url="https://example.com",
            session=SessionConfig(secret_key="s"),
            google_oauth=GoogleOAuthConfig(client_id="c"),
        )
        assert c.port == 9000
        assert c.public_base_url == "https://example.com"
