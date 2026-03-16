"""Authentication service for Google OAuth and session management."""

from datetime import UTC
from datetime import datetime
from urllib.parse import urlencode

import httpx
from loguru import logger as lg

from fastapi_tools.config import GoogleOAuthConfig
from fastapi_tools.config import SessionConfig
from fastapi_tools.schemas.auth import GoogleUserInfo
from fastapi_tools.schemas.auth import SessionData
from fastapi_tools.security import generate_session_id
from fastapi_tools.security import generate_state_token
from fastapi_tools.security import get_expiration_time
from fastapi_tools.security import is_expired

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class SessionStore:
    """In-memory session storage.

    For production, consider using Redis or a database.
    """

    def __init__(self) -> None:
        """Initialize empty session store."""
        self._sessions: dict[str, SessionData] = {}
        self._state_tokens: dict[str, datetime] = {}

    def create_session(self, session_data: SessionData) -> None:
        """Store a new session."""
        self._sessions[session_data.session_id] = session_data
        lg.debug(f"Created session for user {session_data.email}")

    def get_session(self, session_id: str) -> SessionData | None:
        """Retrieve a session by ID."""
        session = self._sessions.get(session_id)
        if session and is_expired(session.expires_at):
            self.delete_session(session_id)
            return None
        return session

    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            lg.debug(f"Deleted session {session_id[:8]}...")

    def store_state_token(self, state: str, ttl_seconds: int = 600) -> None:
        """Store OAuth state token for CSRF protection."""
        self._state_tokens[state] = get_expiration_time(ttl_seconds)

    def validate_state_token(self, state: str) -> bool:
        """Validate and consume a state token."""
        expiration = self._state_tokens.pop(state, None)
        if expiration is None:
            return False
        return not is_expired(expiration)

    def cleanup_expired(self) -> int:
        """Remove expired sessions and state tokens."""
        now = datetime.now(UTC)
        removed = 0

        expired_sessions = [
            sid for sid, data in self._sessions.items() if is_expired(data.expires_at)
        ]
        for sid in expired_sessions:
            del self._sessions[sid]
            removed += 1

        expired_states = [
            state for state, exp in self._state_tokens.items() if now > exp
        ]
        for state in expired_states:
            del self._state_tokens[state]
            removed += 1

        if removed > 0:
            lg.debug(f"Cleaned up {removed} expired sessions/tokens")

        return removed


class GoogleAuthService:
    """Service for Google OAuth 2.0 authentication."""

    def __init__(
        self,
        oauth_config: GoogleOAuthConfig,
        session_config: SessionConfig,
        session_store: SessionStore,
    ) -> None:
        """Initialize auth service.

        Args:
            oauth_config: Google OAuth configuration.
            session_config: Session management configuration.
            session_store: Session storage backend.
        """
        self.oauth_config = oauth_config
        self.session_config = session_config
        self.session_store = session_store

    def get_authorization_url(
        self,
        redirect_uri: str | None = None,
    ) -> tuple[str, str]:
        """Generate Google OAuth authorization URL.

        Args:
            redirect_uri: Override redirect URI (e.g. for reverse-proxy setups).
                If None, uses the value from oauth_config.

        Returns:
            Tuple of (authorization_url, state_token).
        """
        state = generate_state_token()
        self.session_store.store_state_token(state)

        params = {
            "client_id": self.oauth_config.client_id,
            "redirect_uri": redirect_uri or self.oauth_config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.oauth_config.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }

        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return auth_url, state

    def validate_state(self, state: str) -> bool:
        """Validate OAuth state parameter."""
        return self.session_store.validate_state_token(state)

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str | None = None,
    ) -> dict:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from Google.
            redirect_uri: Override redirect URI. Must match the one used during login.

        Returns:
            Token response dictionary.
        """
        data = {
            "client_id": self.oauth_config.client_id,
            "client_secret": self.oauth_config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri or self.oauth_config.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Get user information from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return GoogleUserInfo(**response.json())

    async def authenticate(
        self,
        code: str,
        state: str,
        redirect_uri: str | None = None,
    ) -> SessionData:
        """Complete authentication flow.

        Args:
            code: Authorization code from Google.
            state: State parameter for CSRF validation.
            redirect_uri: Override redirect URI. Must match the one used during login.

        Returns:
            SessionData for the authenticated user.

        Raises:
            ValueError: If the state parameter is invalid.
        """
        if not self.validate_state(state):
            msg = "Invalid state parameter"
            raise ValueError(msg)

        tokens = await self.exchange_code_for_tokens(
            code,
            redirect_uri=redirect_uri,
        )
        access_token = tokens["access_token"]
        user_info = await self.get_user_info(access_token)

        return self.create_session(user_info)

    def create_session(self, user_info: GoogleUserInfo) -> SessionData:
        """Create a new session for authenticated user."""
        now = datetime.now(UTC)
        session = SessionData(
            session_id=generate_session_id(),
            user_id=user_info.sub,
            email=user_info.email,
            name=user_info.name,
            picture=user_info.picture,
            created_at=now,
            expires_at=get_expiration_time(self.session_config.max_age),
        )

        self.session_store.create_session(session)
        lg.info(f"User {user_info.email} authenticated successfully")

        return session

    def get_session(self, session_id: str) -> SessionData | None:
        """Get session by ID."""
        return self.session_store.get_session(session_id)

    def revoke_session(self, session_id: str) -> None:
        """Revoke a session."""
        self.session_store.delete_session(session_id)
