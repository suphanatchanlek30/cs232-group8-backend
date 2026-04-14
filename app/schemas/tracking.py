from datetime import datetime

from pydantic import BaseModel

from app.schemas.public import PaginationMeta


class TrackingResponseData(BaseModel):
    trackingCode: str
    reportId: str
    incidentId: str | None = None
    incidentType: str | None = None
    status: str
    severity: str | None = None
    assignedUnit: str | None = None
    latestUpdatedAt: datetime | None = None


class TimelineEntry(BaseModel):
    status: str
    changedAt: datetime
    note: str | None = None


class TrackingTimelineResponseData(BaseModel):
    timeline: list[TimelineEntry]


class MyIncidentItem(BaseModel):
    incidentId: str
    incidentCode: str
    incidentType: str
    summary: str | None = None
    severity: str
    status: str
    reportCount: int
    firstReportTime: datetime
    latestReportTime: datetime


class MyIncidentListResponseData(BaseModel):
    items: list[MyIncidentItem]
    pagination: PaginationMeta
