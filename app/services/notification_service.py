import math

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.unit import Unit
from app.models.user import User
from app.schemas.notification import (
    NotificationItem,
    NotificationListResponseData,
    NotificationReadResponseData,
    NotifyUnitRequest,
)
from app.schemas.public import PaginationMeta
from app.services.sns_service import sns_service
from app.core.config import settings


class NotificationService:
    @staticmethod
    def get_my_notifications(
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 20,
        is_read: bool | None = None,
    ) -> dict:
        """
        Return notifications addressed to this user OR to their unit.
        """
        filters = [
            Notification.recipient_user_id == user.id,
        ]
        if user.unit_id:
            filters.append(Notification.recipient_unit_id == user.unit_id)

        query = db.query(Notification).filter(or_(*filters))

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size))

        items = (
            query.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = NotificationListResponseData(
            items=[
                NotificationItem(
                    notificationId=str(n.id),
                    incidentId=str(n.incident_id) if n.incident_id else None,
                    channel=n.channel,
                    title=n.title,
                    body=n.body,
                    isRead=n.is_read,
                    sentAt=n.sent_at,
                    createdAt=n.created_at,
                )
                for n in items
            ],
            pagination=PaginationMeta(
                page=page,
                pageSize=page_size,
                totalItems=total_items,
                totalPages=total_pages,
            ),
        )
        return data.model_dump()

    @staticmethod
    def mark_as_read(db: Session, user: User, notification_id: str) -> dict:
        notif = db.query(Notification).filter(Notification.id == notification_id).first()

        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        # ensure the notification belongs to this user or their unit
        is_recipient = notif.recipient_user_id == user.id
        is_unit_recipient = user.unit_id and notif.recipient_unit_id == user.unit_id
        if not is_recipient and not is_unit_recipient:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        notif.is_read = True
        db.commit()
        db.refresh(notif)

        data = NotificationReadResponseData(
            notificationId=str(notif.id),
            isRead=notif.is_read,
        )
        return data.model_dump()

    @staticmethod
    def notify_unit_via_sns(db: Session, payload: NotifyUnitRequest) -> dict:
        unit = db.query(Unit).filter(Unit.name == payload.unitName).first()

        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unit '{payload.unitName}' not found",
            )

        if not unit.sns_topic_arn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit '{unit.name}' does not have an SNS Topic configured",
            )

        frontend_link = settings.FRONTEND_URL

        success = sns_service.publish_to_email_topic(
            topic_arn=unit.sns_topic_arn,
            subject=f"มีรายงานเหตุการณ์ใหม่ถึงหน่วยงาน: {unit.name}",
            message=f"เรียน {unit.name},\n\nระบบ TU Pulse ได้รับแจ้งเหตุการณ์ใหม่ที่เกี่ยวข้องกับหน่วยงานของคุณ\n\nกรุณาเข้าสู่ระบบเพื่อตรวจสอบรายละเอียดเพิ่มเติมที่คลิก: {frontend_link}\n\nขอบคุณครับ\nทีมงาน TU Pulse"
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish message to SNS",
            )

        return {
            "success": True,
            "message": f"Successfully sent SNS notification to unit '{unit.name}'",
            "contact_email": unit.contact_email
        }
