"""Tests for Staff Auth endpoints."""
import uuid

import pytest

from app.core.enums import AuthProvider, UserRole
from app.core.security import hash_password
from app.models.user import User


@pytest.fixture()
def seeded_staff(db):
    """Create a staff user with known credentials (via shared session)."""
    unique = uuid.uuid4().hex[:6]
    user = User(
        role=UserRole.STAFF.value,
        auth_provider=AuthProvider.LOCAL.value,
        email=f"staff-{unique}@tu.ac.th",
        password_hash=hash_password("StaffPass1!"),
        full_name="Staff Test User",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


class TestStaffLogin:
    def test_login_success(self, client, seeded_staff):
        r = client.post("/api/v1/staff/auth/login", json={
            "email": seeded_staff.email,
            "password": "StaffPass1!",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]
        assert body["data"]["user"]["role"] == "STAFF"
        assert body["data"]["user"]["email"] == seeded_staff.email

    def test_login_wrong_password(self, client, seeded_staff):
        r = client.post("/api/v1/staff/auth/login", json={
            "email": seeded_staff.email,
            "password": "WrongPassword!",
        })
        assert r.status_code == 401

    def test_login_email_not_found(self, client):
        r = client.post("/api/v1/staff/auth/login", json={
            "email": "nobody@tu.ac.th",
            "password": "whatever",
        })
        assert r.status_code == 401

    def test_login_reporter_rejected(self, client, reporter_user):
        """Reporter users cannot use staff login (no email/password)."""
        r = client.post("/api/v1/staff/auth/login", json={
            "email": "reporter@test.com",
            "password": "anything",
        })
        assert r.status_code == 401


class TestStaffRefreshLogout:
    def _login(self, client, seeded_staff):
        r = client.post("/api/v1/staff/auth/login", json={
            "email": seeded_staff.email,
            "password": "StaffPass1!",
        })
        data = r.json()["data"]
        return data["accessToken"], data["refreshToken"]

    def test_refresh(self, client, seeded_staff):
        access, refresh = self._login(client, seeded_staff)
        r = client.post("/api/v1/staff/auth/refresh", json={
            "refreshToken": refresh,
        })
        assert r.status_code == 200
        assert "accessToken" in r.json()["data"]

    def test_me(self, client, seeded_staff):
        access, _ = self._login(client, seeded_staff)
        r = client.get("/api/v1/staff/auth/me", headers={
            "Authorization": f"Bearer {access}",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["role"] == "STAFF"
        assert "permissions" in data

    def test_logout_revokes(self, client, seeded_staff):
        _, refresh = self._login(client, seeded_staff)
        r = client.post("/api/v1/staff/auth/logout", json={
            "refreshToken": refresh,
        })
        assert r.status_code == 200
        # refresh should now fail
        r = client.post("/api/v1/staff/auth/refresh", json={
            "refreshToken": refresh,
        })
        assert r.status_code == 403


class TestStaffMeUnauth:
    def test_reporter_cannot_access_staff_me(self, client, auth_header):
        """A REPORTER token should be rejected by staff /me."""
        r = client.get("/api/v1/staff/auth/me", headers=auth_header)
        assert r.status_code == 403
