"""Incidents router — list, detail, actions, timeline, fusion, scoring."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.incident import (
    AddCommentRequest,
    AssignUnitRequest,
    ResolveIncidentRequest,
    UpdatePriorityRequest,
    UpdateStatusRequest,
)
from app.services.incident_service import IncidentService

router = APIRouter()


# ============================================================ LIST
@router.get("", response_model=ApiResponse)
def list_incidents(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    incidentType: str | None = Query(default=None),
    assignedUnitId: str | None = Query(default=None),
    search: str | None = Query(default=None),
    dateFrom: datetime | None = Query(default=None),
    dateTo: datetime | None = Query(default=None),
    sortBy: str = Query(default="latestReportTime"),
    sortOrder: str = Query(default="desc"),
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.list_incidents(
        db,
        page=page,
        page_size=pageSize,
        incident_status=status,
        severity=severity,
        incident_type=incidentType,
        assigned_unit_id=assignedUnitId,
        search=search,
        date_from=dateFrom,
        date_to=dateTo,
        sort_by=sortBy,
        sort_order=sortOrder,
    )
    return ApiResponse(success=True, message="ดึงรายการ incident สำเร็จ", data=data)


# ============================================================ DETAIL
@router.get("/{incidentId}", response_model=ApiResponse)
def get_incident_detail(
    incidentId: str,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.get_incident(db, incidentId)
    return ApiResponse(success=True, message="ดึงรายละเอียด incident สำเร็จ", data=data)


# ============================================================ INCIDENT REPORTS
@router.get("/{incidentId}/reports", response_model=ApiResponse)
def get_incident_reports(
    incidentId: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.get_incident_reports(db, incidentId, page=page, page_size=pageSize)
    return ApiResponse(success=True, message="ดึงรายงานใน incident สำเร็จ", data=data)


# ============================================================ INCIDENT TIMELINE
@router.get("/{incidentId}/timeline", response_model=ApiResponse)
def get_incident_timeline(
    incidentId: str,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.get_incident_timeline(db, incidentId)
    return ApiResponse(success=True, message="ดึงไทม์ไลน์ incident สำเร็จ", data=data)


# ============================================================ UPDATE STATUS
@router.patch("/{incidentId}/status", response_model=ApiResponse)
def update_incident_status(
    incidentId: str,
    payload: UpdateStatusRequest,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.update_status(db, incidentId, payload.status, payload.note, user)
    return ApiResponse(success=True, message="อัปเดตสถานะ incident สำเร็จ", data=data)


# ============================================================ ASSIGN UNIT
@router.patch("/{incidentId}/assign-unit", response_model=ApiResponse)
def assign_unit(
    incidentId: str,
    payload: AssignUnitRequest,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.assign_unit(db, incidentId, payload.assignedUnitId, payload.note, user)
    return ApiResponse(success=True, message="มอบหมายหน่วยงานสำเร็จ", data=data)


# ============================================================ UPDATE PRIORITY
@router.patch("/{incidentId}/priority", response_model=ApiResponse)
def update_priority(
    incidentId: str,
    payload: UpdatePriorityRequest,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.update_priority(db, incidentId, payload.severity, payload.reason, user)
    return ApiResponse(success=True, message="อัปเดต severity สำเร็จ", data=data)


# ============================================================ RESOLVE
@router.post("/{incidentId}/resolve", response_model=ApiResponse)
def resolve_incident(
    incidentId: str,
    payload: ResolveIncidentRequest,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.resolve_incident(
        db, incidentId, payload.resolutionSummary, payload.resolvedAt, user,
    )
    return ApiResponse(success=True, message="ปิด incident สำเร็จ", data=data)


# ============================================================ COMMENTS
@router.post("/{incidentId}/comments", response_model=ApiResponse, status_code=201)
def add_comment(
    incidentId: str,
    payload: AddCommentRequest,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.add_comment(db, incidentId, payload.comment, user)
    return ApiResponse(success=True, message="เพิ่มความคิดเห็นสำเร็จ", data=data)


# ============================================================ FUSION EXPLANATION
@router.get("/{incidentId}/fusion-explanation", response_model=ApiResponse)
def fusion_explanation(
    incidentId: str,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.get_fusion_explanation(db, incidentId)
    return ApiResponse(success=True, message="ดึงเหตุผลการจัดกลุ่มสำเร็จ", data=data)


# ============================================================ SCORING EXPLANATION
@router.get("/{incidentId}/scoring-explanation", response_model=ApiResponse)
def scoring_explanation(
    incidentId: str,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = IncidentService.get_scoring_explanation(db, incidentId)
    return ApiResponse(success=True, message="ดึงเหตุผลการประเมินสำเร็จ", data=data)
