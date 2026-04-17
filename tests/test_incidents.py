"""Tests for Incident endpoints (Dashboard list, detail, actions, timeline, fusion, scoring)."""
import uuid

import pytest

from app.models.unit import Unit


@pytest.fixture()
def _create_incident_via_report(client, auth_header):
    """Helper: create a report with label => creates incident; return report data."""
    r = client.post("/api/v1/reports", json={
        "sourceChannel": "LIFF",
        "reportText": "มีขยะล้นถังหน้าตึก SC",
        "label": "waste_issue",
        "location": {
            "locationName": "หน้าตึก SC",
            "lat": 14.072,
            "lng": 100.601,
        },
    }, headers=auth_header)
    assert r.status_code == 201
    return r.json()["data"]


# ================================================================= AUTH GUARD
class TestIncidentAuthGuard:
    def test_no_auth_rejected(self, client):
        r = client.get("/api/v1/incidents")
        assert r.status_code == 403

    def test_reporter_rejected(self, client, auth_header):
        r = client.get("/api/v1/incidents", headers=auth_header)
        assert r.status_code == 403

    def test_staff_can_access(self, client, staff_auth_header):
        r = client.get("/api/v1/incidents", headers=staff_auth_header)
        assert r.status_code == 200

    def test_admin_can_access(self, client, admin_auth_header):
        r = client.get("/api/v1/incidents", headers=admin_auth_header)
        assert r.status_code == 200


# ================================================================= LIST
class TestIncidentList:
    def test_list_empty(self, client, staff_auth_header):
        r = client.get("/api/v1/incidents", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert "items" in data
        assert "pagination" in data

    def test_list_after_report(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        r = client.get("/api/v1/incidents", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["pagination"]["totalItems"] >= 1

    def test_filter_by_status(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        r = client.get("/api/v1/incidents", params={"status": "NEW"}, headers=staff_auth_header)
        assert r.status_code == 200
        for item in r.json()["data"]["items"]:
            assert item["status"] == "NEW"

    def test_filter_by_type(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        r = client.get("/api/v1/incidents", params={
            "incidentType": "waste_issue",
        }, headers=staff_auth_header)
        assert r.status_code == 200

    def test_search(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        r = client.get("/api/v1/incidents", params={
            "search": "SC",
        }, headers=staff_auth_header)
        assert r.status_code == 200

    def test_pagination(self, client, staff_auth_header):
        r = client.get("/api/v1/incidents", params={
            "page": 1, "pageSize": 5,
        }, headers=staff_auth_header)
        assert r.status_code == 200
        assert r.json()["data"]["pagination"]["pageSize"] == 5


# ================================================================= DETAIL
class TestIncidentDetail:
    def test_get_detail(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.get(f"/api/v1/incidents/{incident_id}", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["incidentId"] == incident_id
        assert data["incidentType"] == "waste_issue"
        assert "severity" in data
        assert "confidence" in data

    def test_detail_not_found(self, client, staff_auth_header):
        r = client.get(f"/api/v1/incidents/{uuid.uuid4()}", headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= INCIDENT REPORTS
class TestIncidentReports:
    def test_get_reports(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.get(f"/api/v1/incidents/{incident_id}/reports", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert "items" in data
        assert data["pagination"]["totalItems"] >= 1

    def test_reports_not_found(self, client, staff_auth_header):
        r = client.get(f"/api/v1/incidents/{uuid.uuid4()}/reports", headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= INCIDENT TIMELINE
class TestIncidentTimeline:
    def test_get_timeline(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.get(f"/api/v1/incidents/{incident_id}/timeline", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert "timeline" in data
        assert len(data["timeline"]) >= 1
        assert data["timeline"][0]["actionType"] == "INCIDENT_CREATED"

    def test_timeline_not_found(self, client, staff_auth_header):
        r = client.get(f"/api/v1/incidents/{uuid.uuid4()}/timeline", headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= UPDATE STATUS
class TestUpdateStatus:
    def test_update_to_in_review(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.patch(f"/api/v1/incidents/{incident_id}/status", json={
            "status": "IN_REVIEW",
            "note": "กำลังตรวจสอบ",
        }, headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "IN_REVIEW"

    def test_invalid_transition(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        # NEW -> RESOLVED is not allowed directly
        r = client.patch(f"/api/v1/incidents/{incident_id}/status", json={
            "status": "RESOLVED",
        }, headers=staff_auth_header)
        assert r.status_code == 409

    def test_not_found(self, client, staff_auth_header):
        r = client.patch(f"/api/v1/incidents/{uuid.uuid4()}/status", json={
            "status": "IN_REVIEW",
        }, headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= ASSIGN UNIT
class TestAssignUnit:
    def test_assign_unit(self, client, db, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        unit = Unit(code=f"AU_{uuid.uuid4().hex[:5].upper()}", name="Facilities", is_active=True)
        db.add(unit)
        db.flush()

        r = client.patch(f"/api/v1/incidents/{incident_id}/assign-unit", json={
            "assignedUnitId": str(unit.id),
            "note": "ส่งต่อให้ฝ่ายอาคารสถานที่",
        }, headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["assignedUnitId"] == str(unit.id)
        assert data["assignedUnitName"] == "Facilities"

    def test_assign_bad_unit(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.patch(f"/api/v1/incidents/{incident_id}/assign-unit", json={
            "assignedUnitId": str(uuid.uuid4()),
        }, headers=staff_auth_header)
        assert r.status_code == 400


# ================================================================= UPDATE PRIORITY
class TestUpdatePriority:
    def test_update_priority(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.patch(f"/api/v1/incidents/{incident_id}/priority", json={
            "severity": "HIGH",
            "reason": "อยู่ใกล้ห้อง server",
        }, headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["severity"] == "HIGH"

    def test_invalid_severity(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.patch(f"/api/v1/incidents/{incident_id}/priority", json={
            "severity": "SUPER_HIGH",
        }, headers=staff_auth_header)
        assert r.status_code == 400


# ================================================================= RESOLVE
class TestResolveIncident:
    def test_resolve_incident(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.post(f"/api/v1/incidents/{incident_id}/resolve", json={
            "resolutionSummary": "เก็บขยะและทำความสะอาดเรียบร้อย",
        }, headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "RESOLVED"

    def test_resolve_already_resolved(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        # resolve first time
        client.post(f"/api/v1/incidents/{incident_id}/resolve", json={
            "resolutionSummary": "Done",
        }, headers=staff_auth_header)

        # resolve second time should fail
        r = client.post(f"/api/v1/incidents/{incident_id}/resolve", json={
            "resolutionSummary": "Done again",
        }, headers=staff_auth_header)
        assert r.status_code == 409

    def test_resolve_not_found(self, client, staff_auth_header):
        r = client.post(f"/api/v1/incidents/{uuid.uuid4()}/resolve", json={
            "resolutionSummary": "Done",
        }, headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= COMMENTS
class TestIncidentComments:
    def test_add_comment(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.post(f"/api/v1/incidents/{incident_id}/comments", json={
            "comment": "รอทีมช่างเข้าพื้นที่",
        }, headers=staff_auth_header)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["comment"] == "รอทีมช่างเข้าพื้นที่"
        assert data["isInternal"] is True
        assert "commentId" in data

    def test_empty_comment_rejected(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.post(f"/api/v1/incidents/{incident_id}/comments", json={
            "comment": "   ",
        }, headers=staff_auth_header)
        assert r.status_code == 400

    def test_comment_not_found(self, client, staff_auth_header):
        r = client.post(f"/api/v1/incidents/{uuid.uuid4()}/comments", json={
            "comment": "test",
        }, headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= FUSION EXPLANATION
class TestFusionExplanation:
    def test_fusion_explanation(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.get(f"/api/v1/incidents/{incident_id}/fusion-explanation", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert "matchRules" in data
        assert "mergedReports" in data
        assert data["mergedReports"] >= 1
        assert "explanationText" in data

    def test_fusion_not_found(self, client, staff_auth_header):
        r = client.get(f"/api/v1/incidents/{uuid.uuid4()}/fusion-explanation", headers=staff_auth_header)
        assert r.status_code == 404


# ================================================================= SCORING EXPLANATION
class TestScoringExplanation:
    def test_scoring_explanation(self, client, auth_header, staff_auth_header, _create_incident_via_report):
        report_data = _create_incident_via_report
        incident_id = report_data["incidentId"]
        if not incident_id:
            pytest.skip("No incident created")

        r = client.get(f"/api/v1/incidents/{incident_id}/scoring-explanation", headers=staff_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["incidentType"] == "waste_issue"
        assert "severity" in data
        assert "confidence" in data
        assert "confidenceFactors" in data
        assert len(data["confidenceFactors"]) >= 1

    def test_scoring_not_found(self, client, staff_auth_header):
        r = client.get(f"/api/v1/incidents/{uuid.uuid4()}/scoring-explanation", headers=staff_auth_header)
        assert r.status_code == 404
