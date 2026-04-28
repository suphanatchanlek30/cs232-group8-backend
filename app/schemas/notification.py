from datetime import datetime

from pydantic import BaseModel

from app.schemas.public import PaginationMeta


class NotificationItem(BaseModel):
    notificationId: str
    incidentId: str | None = None
    channel: str
    title: str
    body: str
    isRead: bool
    sentAt: datetime | None = None
    createdAt: datetime


class NotificationListResponseData(BaseModel):
    items: list[NotificationItem]
    pagination: PaginationMeta


class NotificationReadResponseData(BaseModel):
    notificationId: str
    isRead: bool

class NotifyUnitRequest(BaseModel):
    unitName: str
