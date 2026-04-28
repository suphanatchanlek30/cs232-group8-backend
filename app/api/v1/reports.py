from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_reporter, get_current_user
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.report import CreateReportRequest
from app.services.report_service import ReportService
from app.services.s3_service import s3_service

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
    locationNote: str | None = Form(default=None),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
    images: list[UploadFile] = File(default=[]),
    user=Depends(get_current_reporter),
    db: Session = Depends(get_db),
):
    attachments_data = []
    for img in images:
        if img.filename:
            s3_data = s3_service.upload_file(img, str(user.id))
            if s3_data:
                attachments_data.append(s3_data)

    data = ReportService.create_report_multipart(
        db=db,
        user=user,
        report_text=reportText,
        voice_text=voiceText,
        label=label,
        occurred_at=occurredAt,
        location_name=locationName,
        location_note=locationNote,
        lat=lat,
        lng=lng,
        attachments_data=attachments_data,
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

@router.get("/{reportId}/images", response_model=ApiResponse)
def get_report_image_urls(
    reportId: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ReportService.get_report_images(db, reportId, user)
    return ApiResponse(
        success=True,
        message="ดึงรูปภาพของรายงานสำเร็จ",
        data=data,
    )
