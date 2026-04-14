from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.admin import (
    CreateLocationRequest,
    CreateRoutingRuleRequest,
    CreateStaffUserRequest,
    CreateUnitRequest,
)
from app.schemas.common import ApiResponse
from app.services.admin_service import AdminService

router = APIRouter()


# ============================================================ UNITS
@router.get("/units", response_model=ApiResponse)
def list_units(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = AdminService.list_units(db, page=page, page_size=pageSize)
    return ApiResponse(success=True, message="ดึงรายการหน่วยงานสำเร็จ", data=data)


@router.post("/units", response_model=ApiResponse, status_code=201)
def create_unit(
    payload: CreateUnitRequest,
    user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = AdminService.create_unit(db, payload)
    return ApiResponse(success=True, message="สร้างหน่วยงานสำเร็จ", data=data)


# ============================================================ LOCATIONS
@router.post("/locations", response_model=ApiResponse, status_code=201)
def create_location(
    payload: CreateLocationRequest,
    user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = AdminService.create_location(db, payload)
    return ApiResponse(success=True, message="สร้าง location สำเร็จ", data=data)


# ============================================================ ROUTING RULES
@router.get("/routing-rules", response_model=ApiResponse)
def list_routing_rules(
    user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = AdminService.list_routing_rules(db)
    return ApiResponse(success=True, message="ดึงกฎ routing สำเร็จ", data=data)


@router.post("/routing-rules", response_model=ApiResponse, status_code=201)
def create_routing_rule(
    payload: CreateRoutingRuleRequest,
    user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = AdminService.create_routing_rule(db, payload)
    return ApiResponse(success=True, message="สร้างกฎ routing สำเร็จ", data=data)


# ============================================================ STAFF USERS
@router.post("/staff-users", response_model=ApiResponse, status_code=201)
def create_staff_user(
    payload: CreateStaffUserRequest,
    user=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    data = AdminService.create_staff_user(db, payload)
    return ApiResponse(success=True, message="สร้างบัญชีเจ้าหน้าที่สำเร็จ", data=data)
