"""fastapi_tools package."""

from fastapi_tools.config import GoogleOAuthConfig
from fastapi_tools.config import SessionConfig
from fastapi_tools.config import WebappConfig
from fastapi_tools.dependencies import get_current_user
from fastapi_tools.dependencies import get_optional_user
from fastapi_tools.exceptions import NotAuthenticatedException
from fastapi_tools.exceptions import NotAuthorizedException
from fastapi_tools.exceptions import RateLimitExceededException
from fastapi_tools.factory import create_app
from fastapi_tools.params.load_env import load_env

load_env()

__all__ = [
    "GoogleOAuthConfig",
    "NotAuthenticatedException",
    "NotAuthorizedException",
    "RateLimitExceededException",
    "SessionConfig",
    "WebappConfig",
    "create_app",
    "get_current_user",
    "get_optional_user",
]
