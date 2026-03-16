"""Tests for security utilities."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from fastapi_tools.security import TokenManager
from fastapi_tools.security import generate_session_id
from fastapi_tools.security import generate_state_token
from fastapi_tools.security import get_expiration_time
from fastapi_tools.security import hash_token
from fastapi_tools.security import is_expired
from fastapi_tools.security import sanitize_dict
from fastapi_tools.security import sanitize_html


class TestTokenManager:
    """Tests for the TokenManager class."""

    def test_generate_and_validate_token(self) -> None:
        """Round-trip a token through generate and validate."""
        mgr = TokenManager("test-secret")
        token = mgr.generate_token("hello", salt="test")
        assert mgr.validate_token(token, salt="test") == "hello"

    def test_validate_token_wrong_salt(self) -> None:
        """Wrong salt should return None."""
        mgr = TokenManager("test-secret")
        token = mgr.generate_token("hello", salt="a")
        assert mgr.validate_token(token, salt="b") is None

    def test_validate_token_expired(self) -> None:
        """Expired token should return None when max_age is negative."""
        mgr = TokenManager("test-secret")
        token = mgr.generate_token("hello")
        # Use max_age=-1 to guarantee expiration
        assert mgr.validate_token(token, max_age=-1) is None

    def test_csrf_token_round_trip(self) -> None:
        """CSRF token should validate successfully."""
        mgr = TokenManager("test-secret")
        csrf = mgr.generate_csrf_token()
        assert mgr.validate_csrf_token(csrf) is True

    def test_csrf_token_invalid(self) -> None:
        """Invalid CSRF token should fail validation."""
        mgr = TokenManager("test-secret")
        assert mgr.validate_csrf_token("bogus") is False


class TestHelpers:
    """Tests for standalone helper functions."""

    def test_generate_session_id_length(self) -> None:
        """Session ID should be 64 hex characters."""
        sid = generate_session_id()
        assert len(sid) == 64
        assert all(c in "0123456789abcdef" for c in sid)

    def test_generate_session_id_unique(self) -> None:
        """Two calls should produce different IDs."""
        assert generate_session_id() != generate_session_id()

    def test_generate_state_token_length(self) -> None:
        """State token should be 32 hex characters."""
        tok = generate_state_token()
        assert len(tok) == 32

    def test_hash_token_deterministic(self) -> None:
        """Same input should produce same hash."""
        assert hash_token("abc") == hash_token("abc")

    def test_hash_token_different_inputs(self) -> None:
        """Different inputs should produce different hashes."""
        assert hash_token("abc") != hash_token("xyz")

    def test_sanitize_html_escapes_tags(self) -> None:
        """HTML tags should be escaped."""
        assert sanitize_html("<script>alert(1)</script>") == (
            "&lt;script&gt;alert(1)&lt;/script&gt;"
        )

    def test_sanitize_dict_nested(self) -> None:
        """Nested dicts and lists should be recursively sanitized."""
        data = {
            "name": "<b>user</b>",
            "nested": {"html": "<i>hi</i>"},
            "tags": ["<a>", "ok"],
            "count": 42,
        }
        result = sanitize_dict(data)
        assert result["name"] == "&lt;b&gt;user&lt;/b&gt;"
        assert result["nested"]["html"] == "&lt;i&gt;hi&lt;/i&gt;"
        assert result["tags"] == ["&lt;a&gt;", "ok"]
        assert result["count"] == 42

    def test_get_expiration_time_future(self) -> None:
        """Expiration time should be in the future."""
        exp = get_expiration_time(60)
        assert exp > datetime.now(UTC)

    def test_is_expired_past(self) -> None:
        """A past datetime should be considered expired."""
        past = datetime.now(UTC) - timedelta(seconds=1)
        assert is_expired(past) is True

    def test_is_expired_future(self) -> None:
        """A future datetime should not be expired."""
        future = datetime.now(UTC) + timedelta(seconds=60)
        assert is_expired(future) is False
