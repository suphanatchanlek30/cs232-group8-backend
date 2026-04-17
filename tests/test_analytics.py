"""Tests for Analytics endpoints."""

import pytest


class TestAnalyticsAuthGuard:
    """Analytics endpoints should be accessible without auth for now (no auth guard in router)."""

    def test_kpi_summary_requires_dates(self, client):
        r = client.get("/api/v1/analytics/kpi-summary")
        assert r.status_code == 422  # missing required query params

    def test_incident_type_distribution_requires_dates(self, client):
        r = client.get("/api/v1/analytics/incident-type-distribution")
        assert r.status_code == 422


class TestKpiSummary:
    def test_kpi_summary_empty(self, client):
        r = client.get("/api/v1/analytics/kpi-summary", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalReports"] == 0
        assert data["totalIncidents"] == 0
        assert data["fusionRate"] == 0

    def test_kpi_summary_with_data(self, client, auth_header):
        # create a report with label => creates incident
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "มีขยะล้น",
            "label": "waste_issue",
        }, headers=auth_header)

        r = client.get("/api/v1/analytics/kpi-summary", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2099-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalReports"] >= 1
        assert data["totalIncidents"] >= 1


class TestIncidentTypeDistribution:
    def test_distribution_empty(self, client):
        r = client.get("/api/v1/analytics/incident-type-distribution", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)

    def test_distribution_with_data(self, client, auth_header):
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "ท่อแตก",
            "label": "water_leak",
        }, headers=auth_header)

        r = client.get("/api/v1/analytics/incident-type-distribution", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2099-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) >= 1
        assert any(d["incidentType"] == "water_leak" for d in data)


class TestHotspotLocations:
    def test_hotspots_empty(self, client):
        r = client.get("/api/v1/analytics/hotspot-locations", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)


class TestPeakTimeAnalysis:
    def test_peak_time_empty(self, client):
        r = client.get("/api/v1/analytics/peak-time-analysis", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)


class TestFusionStatistics:
    def test_fusion_stats_empty(self, client):
        r = client.get("/api/v1/analytics/fusion-statistics", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalReports"] == 0
        assert data["fusionRate"] == 0

    def test_fusion_stats_with_data(self, client, auth_header):
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "ไฟไหม้",
            "label": "fire_smoke",
        }, headers=auth_header)

        r = client.get("/api/v1/analytics/fusion-statistics", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2099-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["totalReports"] >= 1


class TestStatusOverview:
    def test_status_overview_empty(self, client):
        r = client.get("/api/v1/analytics/status-overview", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2020-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)

    def test_status_overview_with_data(self, client, auth_header):
        client.post("/api/v1/reports", json={
            "sourceChannel": "LIFF",
            "reportText": "เหตุการณ์ความปลอดภัย",
            "label": "security_issue",
        }, headers=auth_header)

        r = client.get("/api/v1/analytics/status-overview", params={
            "dateFrom": "2020-01-01T00:00:00",
            "dateTo": "2099-12-31T23:59:59",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) >= 1
