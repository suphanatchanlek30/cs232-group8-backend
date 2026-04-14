"""Tests for Admin endpoints."""
import uuid

import pytest

from app.models.unit import Unit


# ================================================================= AUTH GUARD
class TestAdminAuthGuard:
    """All admin endpoints must reject non-admin users."""

    def test_reporter_rejected(self, client, auth_header):
        r = client.get("/api/v1/admin/units", headers=auth_header)
        assert r.status_code == 403

    def test_staff_rejected(self, client, staff_auth_header):
        r = client.get("/api/v1/admin/units", headers=staff_auth_header)
        assert r.status_code == 403

    def test_no_auth_rejected(self, client):
        r = client.get("/api/v1/admin/units")
        assert r.status_code == 403


# ================================================================= UNITS
class TestAdminUnits:
    def test_list_units_empty(self, client, admin_auth_header):
        r = client.get("/api/v1/admin/units", headers=admin_auth_header)
        assert r.status_code == 200
        data = r.json()["data"]
        assert "items" in data
        assert "pagination" in data

    def test_create_unit(self, client, admin_auth_header):
        code = f"U{uuid.uuid4().hex[:5].upper()}"
        r = client.post("/api/v1/admin/units", json={
            "name": "Facilities",
            "code": code,
            "email": "fac@tu.ac.th",
        }, headers=admin_auth_header)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["code"] == code
        assert data["name"] == "Facilities"
        assert data["contactEmail"] == "fac@tu.ac.th"

    def test_create_unit_duplicate_code(self, client, admin_auth_header):
        code = f"DUP{uuid.uuid4().hex[:4].upper()}"
        # first
        client.post("/api/v1/admin/units", json={
            "name": "First", "code": code,
        }, headers=admin_auth_header)
        # duplicate
        r = client.post("/api/v1/admin/units", json={
            "name": "Second", "code": code,
        }, headers=admin_auth_header)
        assert r.status_code == 409

    def test_list_units_after_create(self, client, admin_auth_header):
        code = f"LST{uuid.uuid4().hex[:4].upper()}"
        client.post("/api/v1/admin/units", json={
            "name": "Listed Unit", "code": code,
        }, headers=admin_auth_header)
        r = client.get("/api/v1/admin/units", headers=admin_auth_header)
        assert r.status_code == 200
        assert r.json()["data"]["pagination"]["totalItems"] >= 1


# ================================================================= LOCATIONS
class TestAdminLocations:
    def test_create_location(self, client, admin_auth_header):
        r = client.post("/api/v1/admin/locations", json={
            "locationName": "หน้าตึก LC",
            "buildingCode": "LC",
            "lat": 14.072,
            "lng": 100.601,
        }, headers=admin_auth_header)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["locationName"] == "หน้าตึก LC"
        assert data["buildingCode"] == "LC"
        assert data["lat"] == 14.072

    def test_create_location_minimal(self, client, admin_auth_header):
        r = client.post("/api/v1/admin/locations", json={
            "locationName": "ที่จอดรถ",
        }, headers=admin_auth_header)
        assert r.status_code == 201

    def test_location_appears_in_public(self, client, admin_auth_header):
        """Locations created via admin should appear in public listing."""
        client.post("/api/v1/admin/locations", json={
            "locationName": "Public Search Test",
            "buildingCode": "PST",
        }, headers=admin_auth_header)
        r = client.get("/api/v1/public/locations", params={"search": "Public Search"})
        assert r.status_code == 200
        assert r.json()["data"]["pagination"]["totalItems"] >= 1


# ================================================================= ROUTING RULES
class TestAdminRoutingRules:
    @pytest.fixture()
    def test_unit(self, db):
        unit = Unit(
            code=f"RR_{uuid.uuid4().hex[:5].upper()}",
            name="Rule Test Unit",
            is_active=True,
        )
        db.add(unit)
        db.flush()
        return unit

    def test_list_rules_empty(self, client, admin_auth_header):
        r = client.get("/api/v1/admin/routing-rules", headers=admin_auth_header)
        assert r.status_code == 200
        assert "items" in r.json()["data"]

    def test_create_rule(self, client, admin_auth_header, test_unit):
        r = client.post("/api/v1/admin/routing-rules", json={
            "incidentType": "fire_smoke",
            "severity": "HIGH",
            "assignedUnitId": str(test_unit.id),
        }, headers=admin_auth_header)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["incidentType"] == "fire_smoke"
        assert data["assignedUnitName"] == "Rule Test Unit"

    def test_create_rule_duplicate(self, client, admin_auth_header, test_unit):
        payload = {
            "incidentType": "water_leak",
            "severity": "LOW",
            "assignedUnitId": str(test_unit.id),
        }
        client.post("/api/v1/admin/routing-rules", json=payload, headers=admin_auth_header)
        r = client.post("/api/v1/admin/routing-rules", json=payload, headers=admin_auth_header)
        assert r.status_code == 409

    def test_create_rule_bad_unit(self, client, admin_auth_header):
        r = client.post("/api/v1/admin/routing-rules", json={
            "incidentType": "fire_smoke",
            "assignedUnitId": str(uuid.uuid4()),
        }, headers=admin_auth_header)
        assert r.status_code == 400


# ================================================================= STAFF USERS
class TestAdminStaffUsers:
    def test_create_staff_user(self, client, admin_auth_header):
        email = f"new-staff-{uuid.uuid4().hex[:6]}@tu.ac.th"
        r = client.post("/api/v1/admin/staff-users", json={
            "fullName": "New Staff User",
            "email": email,
            "password": "Password123!",
            "role": "STAFF",
        }, headers=admin_auth_header)
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["email"] == email
        assert data["role"] == "STAFF"

    def test_create_admin_user(self, client, admin_auth_header):
        email = f"new-admin-{uuid.uuid4().hex[:6]}@tu.ac.th"
        r = client.post("/api/v1/admin/staff-users", json={
            "fullName": "New Admin",
            "email": email,
            "password": "Password123!",
            "role": "ADMIN",
        }, headers=admin_auth_header)
        assert r.status_code == 201
        assert r.json()["data"]["role"] == "ADMIN"

    def test_duplicate_email(self, client, admin_auth_header):
        email = f"dup-{uuid.uuid4().hex[:6]}@tu.ac.th"
        client.post("/api/v1/admin/staff-users", json={
            "fullName": "First", "email": email,
            "password": "Password123!", "role": "STAFF",
        }, headers=admin_auth_header)
        r = client.post("/api/v1/admin/staff-users", json={
            "fullName": "Second", "email": email,
            "password": "Password123!", "role": "STAFF",
        }, headers=admin_auth_header)
        assert r.status_code == 409

    def test_invalid_role(self, client, admin_auth_header):
        r = client.post("/api/v1/admin/staff-users", json={
            "fullName": "Bad Role",
            "email": f"bad-{uuid.uuid4().hex[:6]}@tu.ac.th",
            "password": "Password123!",
            "role": "REPORTER",
        }, headers=admin_auth_header)
        assert r.status_code == 400

    def test_with_unit(self, client, admin_auth_header, db):
        unit = Unit(
            code=f"SU_{uuid.uuid4().hex[:5].upper()}",
            name="Staff Unit",
            is_active=True,
        )
        db.add(unit)
        db.flush()

        r = client.post("/api/v1/admin/staff-users", json={
            "fullName": "With Unit",
            "email": f"unit-{uuid.uuid4().hex[:6]}@tu.ac.th",
            "password": "Password123!",
            "role": "STAFF",
            "unitId": str(unit.id),
        }, headers=admin_auth_header)
        assert r.status_code == 201
        assert r.json()["data"]["unitId"] == str(unit.id)
