"""Tests for Tracking endpoints."""


class TestTrackByCode:
    def _create_report(self, client, auth_header):
        r = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "มีคนแอบสูบบุหรี่ในตึก",
            "label": "security_issue",
        }, headers=auth_header)
        return r.json()["data"]

    def test_track_by_code_success(self, client, auth_header):
        report_data = self._create_report(client, auth_header)
        tracking_code = report_data["trackingCode"]

        r = client.get(f"/api/v1/tracking/{tracking_code}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["trackingCode"] == tracking_code
        assert data["reportId"] == report_data["reportId"]
        assert data["status"] is not None

    def test_track_by_code_not_found(self, client):
        r = client.get("/api/v1/tracking/TP-00000000-XXXX")
        assert r.status_code == 404

    def test_track_no_auth_required(self, client, auth_header):
        """Tracking is public — no auth header needed."""
        report_data = self._create_report(client, auth_header)
        tracking_code = report_data["trackingCode"]

        # call WITHOUT auth
        r = client.get(f"/api/v1/tracking/{tracking_code}")
        assert r.status_code == 200


class TestTimeline:
    def test_timeline_has_submitted(self, client, auth_header):
        r = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "น้ำรั่ว",
            "label": "water_leak",
        }, headers=auth_header)
        tc = r.json()["data"]["trackingCode"]

        r = client.get(f"/api/v1/tracking/{tc}/timeline")
        assert r.status_code == 200
        timeline = r.json()["data"]["timeline"]
        assert len(timeline) >= 1
        assert timeline[0]["status"] == "SUBMITTED"

    def test_timeline_not_found(self, client):
        r = client.get("/api/v1/tracking/FAKE-CODE/timeline")
        assert r.status_code == 404


class TestMyIncidents:
    def test_my_incidents_requires_auth(self, client):
        r = client.get("/api/v1/tracking/my-incidents")
        assert r.status_code == 403

    def test_my_incidents_empty(self, client, auth_header):
        r = client.get("/api/v1/tracking/my-incidents", headers=auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["items"] == []

    def test_my_incidents_after_report(self, client, auth_header):
        # create a report with label => should create incident
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "ไฟไหม้!",
            "label": "fire_smoke",
        }, headers=auth_header)

        r = client.get("/api/v1/tracking/my-incidents", headers=auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["pagination"]["totalItems"] >= 1
        assert data["items"][0]["incidentType"] == "fire_smoke"
