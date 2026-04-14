from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.public_service import PublicService

router = APIRouter()


@router.get("/system-info", response_model=ApiResponse)
def get_system_info():
    data = PublicService.get_system_info()
    return ApiResponse(
        success=True,
        message="ดึงข้อมูลระบบสำเร็จ",
        data=data,
    )


@router.get("/report-options", response_model=ApiResponse)
def get_report_options():
    data = PublicService.get_report_options()
    return ApiResponse(
        success=True,
        message="ดึงตัวเลือกฟอร์มสำเร็จ",
        data=data,
    )


@router.get("/locations", response_model=ApiResponse)
def get_locations(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    data = PublicService.get_locations(db, search=search, page=page, page_size=pageSize)
    return ApiResponse(
        success=True,
        message="ดึงรายการสถานที่สำเร็จ",
        data=data,
    )
