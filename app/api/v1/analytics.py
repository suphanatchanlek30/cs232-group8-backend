from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/kpi-summary", response_model=ApiResponse)
def kpi_summary(
    dateFrom: datetime,
    dateTo: datetime,
    unitId: int | None = None,
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_kpi_summary(db, dateFrom, dateTo, unitId)
    return ApiResponse(success=True, message="ดึง KPI summary สำเร็จ", data=data)


@router.get("/incident-type-distribution", response_model=ApiResponse)
def incident_type_distribution(
    dateFrom: datetime,
    dateTo: datetime,
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_incident_type_distribution(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง distribution สำเร็จ", data=data)


@router.get("/hotspot-locations", response_model=ApiResponse)
def hotspot_locations(
    dateFrom: datetime,
    dateTo: datetime,
    limit: int = Query(5),
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_hotspots(db, dateFrom, dateTo, limit)
    return ApiResponse(success=True, message="ดึง hotspot สำเร็จ", data=data)


@router.get("/peak-time-analysis", response_model=ApiResponse)
def peak_time(
    dateFrom: datetime,
    dateTo: datetime,
    groupBy: str = "hour",
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_peak_time(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง peak time สำเร็จ", data=data)


@router.get("/fusion-statistics", response_model=ApiResponse)
def fusion_statistics(
    dateFrom: datetime,
    dateTo: datetime,
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_fusion_stats(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง fusion statistics สำเร็จ", data=data)


@router.get("/status-overview", response_model=ApiResponse)
def status_overview(
    dateFrom: datetime,
    dateTo: datetime,
    db: Session = Depends(get_db),
):
    data = AnalyticsService.get_status_overview(db, dateFrom, dateTo)
    return ApiResponse(success=True, message="ดึง status overview สำเร็จ", data=data)
