"""Tests for Notification endpoints."""
import uuid

import pytest

from app.models.notification import Notification


@pytest.fixture()
def sample_notifications(db, staff_user):
    """Create a few notifications for the staff user."""
    user, _, unit = staff_user
    notifs = []
    for i in range(3):
        n = Notification(
            recipient_user_id=user.id,
            channel="SYSTEM",
            title=f"Test Alert {i + 1}",
            body=f"Body of alert {i + 1}",
            is_read=(i == 0),  # first one is read
        )
        db.add(n)
        notifs.append(n)

    # one notification addressed to the unit (not the user directly)
    unit_notif = Notification(
        recipient_unit_id=unit.id,
        channel="SYSTEM",
        title="Unit Alert",
        body="Alert for the whole unit",
        is_read=False,
    )
    db.add(unit_notif)
    notifs.append(unit_notif)

    db.flush()
    return notifs


class TestGetMyNotifications:
    def test_requires_staff_auth(self, client):
        r = client.get("/api/v1/notifications/my")
        assert r.status_code == 403

    def test_reporter_rejected(self, client, auth_header):
        r = client.get("/api/v1/notifications/my", headers=auth_header)
        assert r.status_code == 403

    def test_empty_list(self, client, staff_auth_header):
        r = client.get("/api/v1/notifications/my", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["items"] == []
        assert data["pagination"]["totalItems"] == 0

    def test_returns_notifications(self, client, staff_auth_header, sample_notifications):
        r = client.get("/api/v1/notifications/my", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        # 3 user-targeted + 1 unit-targeted = 4
        assert data["pagination"]["totalItems"] == 4

    def test_filter_unread(self, client, staff_auth_header, sample_notifications):
        r = client.get(
            "/api/v1/notifications/my",
            params={"isRead": False},
            headers=staff_auth_header,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        # 2 unread user + 1 unread unit = 3
        assert data["pagination"]["totalItems"] == 3
        for item in data["items"]:
            assert item["isRead"] is False

    def test_filter_read(self, client, staff_auth_header, sample_notifications):
        r = client.get(
            "/api/v1/notifications/my",
            params={"isRead": True},
            headers=staff_auth_header,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["pagination"]["totalItems"] == 1
        assert data["items"][0]["isRead"] is True

    def test_pagination(self, client, staff_auth_header, sample_notifications):
        r = client.get(
            "/api/v1/notifications/my",
            params={"page": 1, "pageSize": 2},
            headers=staff_auth_header,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data["items"]) == 2
        assert data["pagination"]["totalPages"] == 2


class TestMarkAsRead:
    def test_mark_as_read(self, client, staff_auth_header, sample_notifications):
        # pick the second one (is_read=False)
        notif_id = str(sample_notifications[1].id)
        r = client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers=staff_auth_header,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["notificationId"] == notif_id
        assert data["isRead"] is True

    def test_not_found(self, client, staff_auth_header):
        fake_id = str(uuid.uuid4())
        r = client.patch(
            f"/api/v1/notifications/{fake_id}/read",
            headers=staff_auth_header,
        )
        assert r.status_code == 404

    def test_other_user_cannot_read(self, client, db, sample_notifications):
        """A different staff user cannot mark another user's notification."""
        from app.core.enums import AuthProvider, UserRole
        from app.core.security import create_access_token, hash_password
        from app.models.user import User

        other = User(
            role=UserRole.STAFF.value,
            auth_provider=AuthProvider.LOCAL.value,
            email=f"other-{uuid.uuid4().hex[:6]}@tu.ac.th",
            password_hash=hash_password("Pass1!"),
            full_name="Other Staff",
            is_active=True,
        )
        db.add(other)
        db.flush()
        token = create_access_token(
            subject=str(other.id),
            extra_data={"role": other.role, "auth_provider": other.auth_provider},
        )

        notif_id = str(sample_notifications[1].id)
        r = client.patch(
            f"/api/v1/notifications/{notif_id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    def test_unit_notification_can_be_read(self, client, staff_auth_header, sample_notifications):
        """Staff can mark unit-addressed notifications as read."""
        unit_notif_id = str(sample_notifications[3].id)  # the unit notification
        r = client.patch(
            f"/api/v1/notifications/{unit_notif_id}/read",
            headers=staff_auth_header,
        )
        assert r.status_code == 200
        assert r.json()["data"]["isRead"] is True
