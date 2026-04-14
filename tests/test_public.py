"""Tests for Public endpoints — no auth required."""


class TestSystemInfo:
    def test_get_system_info(self, client):
        r = client.get("/api/v1/public/system-info")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["systemName"] == "TU Pulse"
        assert body["data"]["version"] == "v1"
        assert "allowReportSubmission" in body["data"]

    def test_system_info_has_project_name(self, client):
        r = client.get("/api/v1/public/system-info")
        assert r.json()["data"]["projectNameEn"] == "Campus Incident Intelligence Platform"


class TestReportOptions:
    def test_get_report_options(self, client):
        r = client.get("/api/v1/public/report-options")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "fire_smoke" in data["incidentLabels"]
        assert "waste_issue" in data["incidentLabels"]
        assert "STUDENT" in data["reporterTypes"]
        assert "STAFF" in data["reporterTypes"]
        assert "VISITOR" in data["reporterTypes"]


class TestLocations:
    def test_get_locations_empty(self, client):
        r = client.get("/api/v1/public/locations")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1

    def test_get_locations_with_search(self, client):
        r = client.get("/api/v1/public/locations", params={"search": "nonexistent"})
        assert r.status_code == 200
        assert r.json()["data"]["pagination"]["totalItems"] == 0

    def test_get_locations_pagination_params(self, client):
        r = client.get("/api/v1/public/locations", params={"page": 1, "pageSize": 5})
        assert r.status_code == 200
        assert r.json()["data"]["pagination"]["pageSize"] == 5
