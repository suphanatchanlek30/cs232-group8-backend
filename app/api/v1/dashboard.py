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
