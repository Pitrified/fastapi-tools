"""Tests for auth and common schemas."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from fastapi_tools.schemas.auth import AuthURLResponse
from fastapi_tools.schemas.auth import GoogleUserInfo
from fastapi_tools.schemas.auth import LogoutResponse
from fastapi_tools.schemas.auth import SessionData
from fastapi_tools.schemas.auth import UserResponse
from fastapi_tools.schemas.common import ErrorResponse
from fastapi_tools.schemas.common import HealthResponse
from fastapi_tools.schemas.common import MessageResponse
from fastapi_tools.schemas.common import PaginatedResponse
from fastapi_tools.schemas.common import PaginationParams
from fastapi_tools.schemas.common import ReadinessResponse


class TestAuthSchemas:
    """Tests for authentication schemas."""

    def test_google_user_info_required_fields(self) -> None:
        """Construct GoogleUserInfo with required fields only."""
        info = GoogleUserInfo(sub="123", email="a@b.com", name="A B")
        assert info.sub == "123"
        assert info.email_verified is False
        assert info.picture is None

    def test_session_data_fields(self) -> None:
        """Construct SessionData and verify fields."""
        now = datetime.now(UTC)
        sd = SessionData(
            session_id="sid",
            user_id="uid",
            email="a@b.com",
            name="A",
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
        assert sd.session_id == "sid"
        assert sd.picture is None

    def test_user_response_from_session(self) -> None:
        """UserResponse.from_session should map correctly."""
        now = datetime.now(UTC)
        sd = SessionData(
            session_id="sid",
            user_id="uid",
            email="a@b.com",
            name="A",
            picture="http://pic",
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
        ur = UserResponse.from_session(sd)
        assert ur.id == "uid"
        assert ur.email == "a@b.com"
        assert ur.picture == "http://pic"

    def test_logout_response_default(self) -> None:
        """Default message should be present."""
        resp = LogoutResponse()
        assert resp.message == "Logout successful"

    def test_auth_url_response(self) -> None:
        """Construct AuthURLResponse."""
        resp = AuthURLResponse(auth_url="https://...", state="abc")
        assert resp.state == "abc"


class TestCommonSchemas:
    """Tests for common schemas."""

    def test_health_response(self) -> None:
        """Construct HealthResponse."""
        resp = HealthResponse(
            status="healthy",
            version="1.0",
            timestamp=datetime.now(UTC),
        )
        assert resp.status == "healthy"

    def test_readiness_response(self) -> None:
        """Construct ReadinessResponse with checks."""
        resp = ReadinessResponse(status="ready", checks={"db": True})
        assert resp.checks["db"] is True

    def test_error_response_defaults(self) -> None:
        """Optional fields default to None."""
        resp = ErrorResponse(detail="oops")
        assert resp.error_code is None
        assert resp.request_id is None

    def test_message_response(self) -> None:
        """Construct MessageResponse."""
        resp = MessageResponse(message="ok")
        assert resp.message == "ok"

    def test_pagination_offset(self) -> None:
        """Offset calculation is correct."""
        p = PaginationParams(page=3, page_size=10)
        assert p.offset == 20

    def test_paginated_response_calculate_pages(self) -> None:
        """Pages calculation is correct."""
        assert PaginatedResponse.calculate_pages(0, 10) == 0
        assert PaginatedResponse.calculate_pages(1, 10) == 1
        assert PaginatedResponse.calculate_pages(10, 10) == 1
        assert PaginatedResponse.calculate_pages(11, 10) == 2
