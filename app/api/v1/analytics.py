from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/kpi-summary", response_model=ApiResponse)
def kpi_summary(
    dateFrom: datetime | None = None,
    dateTo: datetime | None = None,
    unitId: str | None = None,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_kpi_summary(db, dateFrom, dateTo, unitId)
    return ApiResponse(success=True, message="ดึง KPI summary สำเร็จ", data=data)


@router.get("/incident-type-distribution", response_model=ApiResponse)
def incident_type_distribution(
    dateFrom: datetime | None = None,
    dateTo: datetime | None = None,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_incident_type_distribution(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง distribution สำเร็จ", data=data)


@router.get("/hotspot-locations", response_model=ApiResponse)
def hotspot_locations(
    dateFrom: datetime | None = None,
    dateTo: datetime | None = None,
    limit: int = Query(5),
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_hotspots(db, dateFrom, dateTo, limit)
    return ApiResponse(success=True, message="ดึง hotspot สำเร็จ", data=data)


@router.get("/peak-time-analysis", response_model=ApiResponse)
def peak_time(
    dateFrom: datetime | None = None,
    dateTo: datetime | None = None,
    groupBy: str = "hour",
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    if groupBy not in {"hour", "day"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid groupBy, allowed values are 'hour' or 'day'",
        )

    data = AnalyticsService.get_peak_time(db, dateFrom, dateTo, groupBy)
    return ApiResponse(success=True, message="ดึง peak time สำเร็จ", data=data)


@router.get("/fusion-statistics", response_model=ApiResponse)
def fusion_statistics(
    dateFrom: datetime | None = None,
    dateTo: datetime | None = None,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_fusion_stats(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง fusion statistics สำเร็จ", data=data)


@router.get("/status-overview", response_model=ApiResponse)
def status_overview(
    dateFrom: datetime | None = None,
    dateTo: datetime | None = None,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_status_overview(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง status overview สำเร็จ", data=data)
