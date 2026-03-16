"""FastAPI dependency injection functions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Annotated

from fastapi import Cookie
from fastapi import Depends
from fastapi import Request

from fastapi_tools.exceptions import NotAuthenticatedException
from fastapi_tools.schemas.auth import SessionData  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Generator

    from fastapi_tools.auth.google import SessionStore


def get_session_store(request: Request) -> SessionStore:
    """Get session store from app state."""
    return request.app.state.session_store


async def get_current_session(
    request: Request,
    session: Annotated[str | None, Cookie(alias="session")] = None,
) -> SessionData | None:
    """Get the current session from the session cookie, if any."""
    if not session:
        return None
    session_store = get_session_store(request)
    return session_store.get_session(session)


async def get_current_user(
    session: Annotated[SessionData | None, Depends(get_current_session)],
) -> SessionData:
    """Require an authenticated user; raises NotAuthenticatedException otherwise."""
    if session is None:
        raise NotAuthenticatedException
    return session


async def get_optional_user(
    session: Annotated[SessionData | None, Depends(get_current_session)],
) -> SessionData | None:
    """Get the current user if authenticated, or None."""
    return session


def get_db_session() -> Generator[None]:
    """Yield a placeholder database session."""
    yield None
