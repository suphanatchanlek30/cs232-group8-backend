"""Dashboard router — KPI summary for staff/admin."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=ApiResponse)
def get_dashboard_summary(
    dateFrom: datetime | None = Query(default=None),
    dateTo: datetime | None = Query(default=None),
    unitId: str | None = Query(default=None),
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = DashboardService.get_summary(
        db, date_from=dateFrom, date_to=dateTo, unit_id=unitId,
    )
    return ApiResponse(
        success=True,
        message="ดึงข้อมูลสรุป dashboard สำเร็จ",
        data=data,
    )


@router.get("/metadata", response_model=ApiResponse)
def get_dashboard_metadata(
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    """Get metadata for dashboard (units, status options, etc)."""
    # Import here to avoid circular imports if any
    from app.services.admin_service import AdminService
    
    units = AdminService.list_units(db, page=1, page_size=100)
    
    status_options = [
        {"value": "NEW", "label": "ใหม่"},
        {"value": "IN_REVIEW", "label": "กำลังตรวจสอบ"},
        {"value": "ROUTED", "label": "ส่งต่อแล้ว"},
        {"value": "IN_PROGRESS", "label": "กำลังดำเนินการ"},
        {"value": "RESOLVED", "label": "เสร็จสิ้น"},
        {"value": "REJECTED", "label": "ปฏิเสธ/ไม่เกี่ยวข้อง"},
    ]
    
    return ApiResponse(
        success=True,
        message="ดึงข้อมูล metadata สำเร็จ",
        data={
            "units": units["items"],
            "statusOptions": status_options
        },
    )
