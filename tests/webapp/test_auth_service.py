"""Tests for SessionStore and GoogleAuthService basics."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from fastapi_tools.auth.google import SessionStore
from fastapi_tools.schemas.auth import SessionData


def _make_session(
    session_id: str = "sid",
    *,
    expired: bool = False,
) -> SessionData:
    now = datetime.now(UTC)
    return SessionData(
        session_id=session_id,
        user_id="uid",
        email="a@b.com",
        name="A",
        created_at=now,
        expires_at=now + timedelta(hours=-1 if expired else 1),
    )


class TestSessionStore:
    """Tests for in-memory SessionStore."""

    def test_create_and_get_session(self) -> None:
        """Create a session and retrieve it."""
        store = SessionStore()
        sd = _make_session()
        store.create_session(sd)
        assert store.get_session("sid") is sd

    def test_get_missing_session(self) -> None:
        """Non-existent session returns None."""
        store = SessionStore()
        assert store.get_session("nope") is None

    def test_get_expired_session_deletes(self) -> None:
        """Expired session is removed on access and returns None."""
        store = SessionStore()
        sd = _make_session(expired=True)
        store.create_session(sd)
        assert store.get_session("sid") is None

    def test_delete_session(self) -> None:
        """Delete a session by ID."""
        store = SessionStore()
        store.create_session(_make_session())
        store.delete_session("sid")
        assert store.get_session("sid") is None

    def test_state_token_round_trip(self) -> None:
        """Store and validate a state token."""
        store = SessionStore()
        store.store_state_token("abc")
        assert store.validate_state_token("abc") is True

    def test_state_token_consumed(self) -> None:
        """State token is consumed after validation."""
        store = SessionStore()
        store.store_state_token("abc")
        store.validate_state_token("abc")
        assert store.validate_state_token("abc") is False

    def test_state_token_missing(self) -> None:
        """Missing state token is invalid."""
        store = SessionStore()
        assert store.validate_state_token("nope") is False

    def test_cleanup_expired(self) -> None:
        """Cleanup should remove expired sessions and tokens."""
        store = SessionStore()
        store.create_session(_make_session(expired=True))
        removed = store.cleanup_expired()
        assert removed >= 1
