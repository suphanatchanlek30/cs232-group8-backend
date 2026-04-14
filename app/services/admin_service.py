import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import AuthProvider, UserRole
from app.core.security import hash_password
from app.models.location import Location
from app.models.routing_rule import RoutingRule
from app.models.unit import Unit
from app.models.user import User
from app.schemas.admin import (
    CreateLocationRequest,
    CreateRoutingRuleRequest,
    CreateStaffUserRequest,
    CreateUnitRequest,
    LocationCreatedResponseData,
    RoutingRuleItem,
    RoutingRuleListResponseData,
    StaffUserCreatedResponseData,
    UnitItem,
    UnitListResponseData,
)
from app.schemas.public import PaginationMeta


class AdminService:
    # ============================================================ UNITS
    @staticmethod
    def list_units(db: Session, page: int = 1, page_size: int = 20) -> dict:
        query = db.query(Unit)
        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size))

        items = (
            query.order_by(Unit.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = UnitListResponseData(
            items=[
                UnitItem(
                    unitId=str(u.id),
                    code=u.code,
                    name=u.name,
                    contactEmail=u.contact_email,
                    description=u.description,
                    isActive=u.is_active,
                )
                for u in items
            ],
            pagination=PaginationMeta(
                page=page, pageSize=page_size,
                totalItems=total_items, totalPages=total_pages,
            ),
        )
        return data.model_dump()

    @staticmethod
    def create_unit(db: Session, payload: CreateUnitRequest) -> dict:
        existing = db.query(Unit).filter(Unit.code == payload.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Unit code '{payload.code}' already exists",
            )

        unit = Unit(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            contact_email=payload.email,
            is_active=True,
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)

        return UnitItem(
            unitId=str(unit.id),
            code=unit.code,
            name=unit.name,
            contactEmail=unit.contact_email,
            description=unit.description,
            isActive=unit.is_active,
        ).model_dump()

    # ============================================================ LOCATIONS
    @staticmethod
    def create_location(db: Session, payload: CreateLocationRequest) -> dict:
        loc = Location(
            location_name=payload.locationName,
            building_code=payload.buildingCode,
            campus_zone=payload.campusZone,
            lat=payload.lat,
            lng=payload.lng,
            is_active=True,
        )
        db.add(loc)
        db.commit()
        db.refresh(loc)

        return LocationCreatedResponseData(
            locationId=str(loc.id),
            locationName=loc.location_name,
            buildingCode=loc.building_code,
            lat=float(loc.lat) if loc.lat is not None else None,
            lng=float(loc.lng) if loc.lng is not None else None,
        ).model_dump()

    # ============================================================ ROUTING RULES
    @staticmethod
    def list_routing_rules(db: Session) -> dict:
        rules = (
            db.query(RoutingRule)
            .filter(RoutingRule.is_active.is_(True))
            .order_by(RoutingRule.incident_type, RoutingRule.priority)
            .all()
        )

        items: list[RoutingRuleItem] = []
        for r in rules:
            unit_name = None
            unit = db.query(Unit).filter(Unit.id == r.assigned_unit_id).first()
            if unit:
                unit_name = unit.name

            items.append(RoutingRuleItem(
                ruleId=str(r.id),
                incidentType=r.incident_type,
                severity=r.severity,
                assignedUnitId=str(r.assigned_unit_id),
                assignedUnitName=unit_name,
                priority=r.priority,
                isActive=r.is_active,
            ))

        return RoutingRuleListResponseData(items=items).model_dump()

    @staticmethod
    def create_routing_rule(db: Session, payload: CreateRoutingRuleRequest) -> dict:
        # check unit exists
        unit = db.query(Unit).filter(Unit.id == payload.assignedUnitId).first()
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned unit not found",
            )

        # check for duplicate
        existing = (
            db.query(RoutingRule)
            .filter(
                RoutingRule.incident_type == payload.incidentType,
                RoutingRule.severity == payload.severity,
                RoutingRule.assigned_unit_id == payload.assignedUnitId,
                RoutingRule.is_active.is_(True),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate routing rule",
            )

        rule = RoutingRule(
            incident_type=payload.incidentType,
            severity=payload.severity,
            assigned_unit_id=payload.assignedUnitId,
            priority=payload.priority,
            is_active=True,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)

        return RoutingRuleItem(
            ruleId=str(rule.id),
            incidentType=rule.incident_type,
            severity=rule.severity,
            assignedUnitId=str(rule.assigned_unit_id),
            assignedUnitName=unit.name,
            priority=rule.priority,
            isActive=rule.is_active,
        ).model_dump()

    # ============================================================ STAFF USERS
    @staticmethod
    def create_staff_user(db: Session, payload: CreateStaffUserRequest) -> dict:
        if payload.role not in (UserRole.STAFF.value, UserRole.ADMIN.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be STAFF or ADMIN",
            )

        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )

        unit_id = None
        if payload.unitId:
            unit = db.query(Unit).filter(Unit.id == payload.unitId).first()
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unit not found",
                )
            unit_id = unit.id

        user = User(
            role=payload.role,
            auth_provider=AuthProvider.LOCAL.value,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.fullName,
            unit_id=unit_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return StaffUserCreatedResponseData(
            userId=str(user.id),
            fullName=user.full_name,
            email=user.email,
            role=user.role,
            unitId=str(user.unit_id) if user.unit_id else None,
        ).model_dump()
