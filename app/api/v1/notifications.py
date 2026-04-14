from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/my", response_model=ApiResponse)
def get_my_notifications(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    isRead: bool | None = Query(default=None),
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = NotificationService.get_my_notifications(
        db, user, page=page, page_size=pageSize, is_read=isRead,
    )
    return ApiResponse(
        success=True,
        message="ดึงรายการแจ้งเตือนสำเร็จ",
        data=data,
    )


@router.patch("/{notificationId}/read", response_model=ApiResponse)
def mark_notification_read(
    notificationId: str,
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = NotificationService.mark_as_read(db, user, notificationId)
    return ApiResponse(
        success=True,
        message="อ่านแจ้งเตือนแล้ว",
        data=data,
    )
