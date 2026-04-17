"""Tests for Dashboard endpoints."""


class TestDashboardSummary:
    def test_requires_staff_auth(self, client):
        r = client.get("/api/v1/dashboard/summary")
        assert r.status_code == 403

    def test_reporter_rejected(self, client, auth_header):
        r = client.get("/api/v1/dashboard/summary", headers=auth_header)
        assert r.status_code == 403

    def test_summary_empty(self, client, staff_auth_header):
        r = client.get("/api/v1/dashboard/summary", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalIncidents"] >= 0
        assert "newCount" in data
        assert "inReviewCount" in data
        assert "inProgressCount" in data
        assert "resolvedCount" in data
        assert "highSeverityCount" in data

    def test_summary_after_report_creates_incident(self, client, auth_header, staff_auth_header):
        # reporter creates a report with label => creates an incident
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "ไฟไหม้ตึก SC",
            "label": "fire_smoke",
        }, headers=auth_header)

        r = client.get("/api/v1/dashboard/summary", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalIncidents"] >= 1
        assert data["newCount"] >= 1

    def test_summary_with_date_filter(self, client, staff_auth_header):
        r = client.get("/api/v1/dashboard/summary", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        }, headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalIncidents"] == 0

    def test_admin_can_access(self, client, admin_auth_header):
        r = client.get("/api/v1/dashboard/summary", headers=admin_auth_header)
        assert r.status_code == 200
