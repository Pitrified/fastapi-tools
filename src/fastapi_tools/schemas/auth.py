"""Authentication-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class GoogleUserInfo(BaseModel):
    """User information returned by the Google userinfo endpoint."""

    sub: str = Field(description="Google user ID (subject)")
    email: EmailStr = Field(description="User email address")
    email_verified: bool = Field(
        default=False,
        description="Whether email is verified",
    )
    name: str = Field(description="User display name")
    picture: str | None = Field(default=None, description="Profile picture URL")
    given_name: str | None = Field(default=None, description="First name")
    family_name: str | None = Field(default=None, description="Last name")


class SessionData(BaseModel):
    """Represents an active user session."""

    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="Google user ID (sub)")
    email: str = Field(description="User email")
    name: str = Field(description="User display name")
    picture: str | None = Field(default=None, description="Profile picture URL")
    created_at: datetime = Field(description="Session creation time")
    expires_at: datetime = Field(description="Session expiration time")


class LoginResponse(BaseModel):
    """Response after successful login."""

    message: str = Field(default="Login successful")
    user: "UserResponse" = Field(description="Authenticated user info")


class UserResponse(BaseModel):
    """Public representation of a user."""

    id: str = Field(description="User ID")
    email: str = Field(description="User email")
    name: str = Field(description="User display name")
    picture: str | None = Field(default=None, description="Profile picture URL")

    @classmethod
    def from_session(cls, session: SessionData) -> "UserResponse":
        """Create a UserResponse from session data."""
        return cls(
            id=session.user_id,
            email=session.email,
            name=session.name,
            picture=session.picture,
        )


class LogoutResponse(BaseModel):
    """Response after logout."""

    message: str = Field(default="Logout successful")


class AuthURLResponse(BaseModel):
    """Response containing Google OAuth authorization URL."""

    auth_url: str = Field(description="Google OAuth authorization URL")
    state: str = Field(description="State parameter for CSRF protection")
