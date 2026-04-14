from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_reporter
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.tracking_service import TrackingService

router = APIRouter()


@router.get("/my-incidents", response_model=ApiResponse)
def get_my_incidents(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    user=Depends(get_current_reporter),
    db: Session = Depends(get_db),
):
    data = TrackingService.get_my_incidents(db, user, page=page, page_size=pageSize)
    return ApiResponse(
        success=True,
        message="ดึงรายการเหตุการณ์ของคุณสำเร็จ",
        data=data,
    )


@router.get("/{trackingCode}", response_model=ApiResponse)
def track_by_code(
    trackingCode: str,
    db: Session = Depends(get_db),
):
    data = TrackingService.track_by_code(db, trackingCode)
    return ApiResponse(
        success=True,
        message="ดึงสถานะการแจ้งเหตุสำเร็จ",
        data=data,
    )


@router.get("/{trackingCode}/timeline", response_model=ApiResponse)
def get_timeline(
    trackingCode: str,
    db: Session = Depends(get_db),
):
    data = TrackingService.get_timeline(db, trackingCode)
    return ApiResponse(
        success=True,
        message="ดึงไทม์ไลน์สำเร็จ",
        data=data,
    )
