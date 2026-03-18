"""Authentication router for Google OAuth endpoints."""

from typing import TYPE_CHECKING
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi.responses import RedirectResponse
import httpx
from loguru import logger as lg

from fastapi_tools.auth.google import GoogleAuthService
from fastapi_tools.dependencies import get_current_session
from fastapi_tools.dependencies import get_current_user
from fastapi_tools.schemas.auth import AuthURLResponse
from fastapi_tools.schemas.auth import LogoutResponse
from fastapi_tools.schemas.auth import SessionData
from fastapi_tools.schemas.auth import UserResponse

if TYPE_CHECKING:
    from fastapi_tools.config import WebappConfig

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(request: Request) -> GoogleAuthService:
    """Get auth service from app state."""
    return request.app.state.auth_service


@router.get(
    "/google/login",
    response_model=None,
    summary="Get Google OAuth URL",
    description="Returns the Google OAuth authorization URL for login.",
)
async def google_login(
    request: Request,
    auth_service: Annotated[GoogleAuthService, Depends(get_auth_service)],
    *,
    redirect: Annotated[
        bool,
        Query(description="Redirect to Google if true, else return URL."),
    ] = True,
) -> AuthURLResponse | RedirectResponse:
    """Initiate Google OAuth login flow."""
    config: WebappConfig = request.app.state.config
    redirect_uri = config.google_oauth.redirect_uri
    auth_url, state = auth_service.get_authorization_url(redirect_uri=redirect_uri)

    if redirect:
        return RedirectResponse(url=auth_url, status_code=302)

    return AuthURLResponse(auth_url=auth_url, state=state)


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    description="Handles the OAuth callback from Google after user authorization.",
)
async def google_callback(
    request: Request,
    auth_service: Annotated[GoogleAuthService, Depends(get_auth_service)],
    code: Annotated[str, Query(description="Authorization code from Google")],
    state: Annotated[str, Query(description="State parameter for CSRF protection")],
    error: Annotated[str | None, Query(description="Error from Google OAuth")] = None,
) -> RedirectResponse:
    """Handle Google OAuth callback."""
    if error:
        lg.warning(f"OAuth error: {error}")
        return RedirectResponse(url=f"/?error={error}", status_code=302)

    try:
        config: WebappConfig = request.app.state.config
        redirect_uri = config.google_oauth.redirect_uri
        session = await auth_service.authenticate(
            code,
            state,
            redirect_uri=redirect_uri,
        )

        redirect_response = RedirectResponse(url="/dashboard", status_code=302)
        redirect_response.set_cookie(
            key=config.session.session_cookie_name,
            value=session.session_id,
            max_age=config.session.max_age,
            httponly=True,
            secure=config.session.https_only,
            samesite=config.session.same_site,
        )
    except ValueError as e:
        lg.warning(f"Auth validation error: {e}")
        return RedirectResponse(url="/?error=invalid_state", status_code=302)
    except httpx.HTTPError as e:
        lg.exception(f"OAuth callback HTTP error: {e}")
        return RedirectResponse(url="/?error=auth_failed", status_code=302)
    else:
        return redirect_response


@router.post(
    "/logout",
    response_model=None,
    summary="Logout",
    description="Invalidates the current session and clears the session cookie.",
)
async def logout(
    request: Request,
    session: Annotated[SessionData, Depends(get_current_user)],
    auth_service: Annotated[GoogleAuthService, Depends(get_auth_service)],
) -> LogoutResponse | RedirectResponse:
    """Logout current user.

    For browser requests returns a redirect to landing page.
    For HTMX requests returns an HX-Redirect header.
    For API requests returns JSON.
    """
    auth_service.revoke_session(session.session_id)
    lg.info(f"User {session.email} logged out")

    config: WebappConfig = request.app.state.config
    cookie_kwargs = {
        "key": config.session.session_cookie_name,
        "httponly": True,
        "secure": config.session.https_only,
        "samesite": config.session.same_site,
    }

    # HTMX requests: return 200 with HX-Redirect header
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.delete_cookie(**cookie_kwargs)
        response.headers["HX-Redirect"] = "/"
        return response  # type: ignore[return-value]

    # Browser requests (Accept: text/html)
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        redirect_resp = RedirectResponse(url="/", status_code=302)
        redirect_resp.delete_cookie(**cookie_kwargs)
        return redirect_resp

    # API / JSON requests
    response = Response(
        content=LogoutResponse().model_dump_json(),
        media_type="application/json",
    )
    response.delete_cookie(**cookie_kwargs)
    return response  # type: ignore[return-value]


@router.get(
    "/me",
    summary="Get current user",
    description="Returns information about the currently authenticated user.",
)
async def get_current_user_info(
    session: Annotated[SessionData, Depends(get_current_user)],
) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse.from_session(session)


@router.get(
    "/status",
    summary="Check authentication status",
    description="Returns authentication status without requiring authentication.",
)
async def auth_status(
    session: Annotated[SessionData | None, Depends(get_current_session)],
) -> dict:
    """Check if user is authenticated."""
    if session:
        return {
            "authenticated": True,
            "user": UserResponse.from_session(session).model_dump(),
        }

    return {"authenticated": False, "user": None}
