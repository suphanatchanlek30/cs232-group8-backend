from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_reporter, get_current_user
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.report import CreateReportRequest
from app.services.report_service import ReportService

router = APIRouter()


@router.post("", response_model=ApiResponse, status_code=201)
def create_report(
    payload: CreateReportRequest,
    user=Depends(get_current_reporter),
    db: Session = Depends(get_db),
):
    data = ReportService.create_report(db, user, payload)
    return ApiResponse(
        success=True,
        message="ส่งรายงานแจ้งเหตุสำเร็จ",
        data=data,
    )


@router.post("/multipart", response_model=ApiResponse, status_code=201)
def create_report_multipart(
    reportText: str | None = Form(default=None),
    voiceText: str | None = Form(default=None),
    label: str | None = Form(default=None),
    occurredAt: datetime | None = Form(default=None),
    locationName: str | None = Form(default=None),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
    images: list[UploadFile] = File(default=[]),
    user=Depends(get_current_reporter),
    db: Session = Depends(get_db),
):
    # For prototype: store file names as URLs (real impl would upload to S3)
    image_urls = [f"/uploads/{img.filename}" for img in images if img.filename]

    data = ReportService.create_report_multipart(
        db=db,
        user=user,
        report_text=reportText,
        voice_text=voiceText,
        label=label,
        occurred_at=occurredAt,
        location_name=locationName,
        lat=lat,
        lng=lng,
        image_urls=image_urls,
    )
    return ApiResponse(
        success=True,
        message="ส่งรายงานแจ้งเหตุสำเร็จ",
        data=data,
    )


@router.get("/my", response_model=ApiResponse)
def get_my_reports(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    user=Depends(get_current_reporter),
    db: Session = Depends(get_db),
):
    data = ReportService.get_my_reports(
        db, user, page=page, page_size=pageSize, report_status=status
    )
    return ApiResponse(
        success=True,
        message="ดึงรายงานของคุณสำเร็จ",
        data=data,
    )


@router.get("/{reportId}", response_model=ApiResponse)
def get_report_detail(
    reportId: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ReportService.get_report(db, reportId, user)
    return ApiResponse(
        success=True,
        message="ดึงรายละเอียดรายงานสำเร็จ",
        data=data,
    )
