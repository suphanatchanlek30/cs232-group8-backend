"""Tests for Report endpoints."""
import pytest


class TestCreateReport:
    def test_create_report_json(self, client, auth_header):
        r = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "มีขยะล้นหน้าตึก LC",
            "label": "waste_issue",
            "location": {
                "locationName": "หน้าตึก LC",
                "lat": 14.072,
                "lng": 100.601,
            },
        }, headers=auth_header)
        assert r.status_code == 201
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert data["trackingCode"].startswith("TP-")
        assert data["status"] in ("SUBMITTED", "LINKED_TO_INCIDENT")
        assert data["candidateIncidentType"] == "waste_issue"

    def test_create_report_without_label(self, client, auth_header):
        r = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "Something happened",
        }, headers=auth_header)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["incidentId"] is None  # no label = no incident
        assert data["status"] == "SUBMITTED"

    def test_create_report_unauth(self, client):
        r = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "test",
        })
        assert r.status_code == 403


class TestMyReports:
    def test_get_my_reports_empty(self, client, auth_header):
        r = client.get("/api/v1/reports/my", headers=auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["items"] == []
        assert data["pagination"]["totalItems"] == 0

    def test_get_my_reports_after_create(self, client, auth_header):
        # create one
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "ไฟดับตึก SC",
            "label": "facility_issue",
        }, headers=auth_header)
        # fetch
        r = client.get("/api/v1/reports/my", headers=auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["pagination"]["totalItems"] >= 1


class TestReportDetail:
    def test_get_report_detail_owner(self, client, auth_header):
        # create
        cr = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "ท่อน้ำแตก",
            "label": "water_leak",
        }, headers=auth_header)
        report_id = cr.json()["data"]["reportId"]

        # get detail
        r = client.get(f"/api/v1/reports/{report_id}", headers=auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["reportId"] == report_id
        assert data["reportText"] == "ท่อน้ำแตก"
        assert "water_leak" in data["detectedLabels"]

    def test_get_report_detail_staff_can_access(self, client, auth_header, staff_auth_header):
        # reporter creates
        cr = client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "test access",
        }, headers=auth_header)
        report_id = cr.json()["data"]["reportId"]

        # staff accesses
        r = client.get(f"/api/v1/reports/{report_id}", headers=staff_auth_header)
        assert r.status_code == 200

    def test_get_report_not_found(self, client, auth_header):
        import uuid
        r = client.get(f"/api/v1/reports/{uuid.uuid4()}", headers=auth_header)
        assert r.status_code == 404
