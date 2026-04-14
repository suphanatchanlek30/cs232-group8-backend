from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.public import PaginationMeta


# ---- request ----

class ReportLocationInput(BaseModel):
    locationId: str | None = None
    locationName: str | None = None
    lat: float | None = None
    lng: float | None = None


class ReportAttachmentInput(BaseModel):
    fileKey: str
    fileUrl: str
    fileType: str = "IMAGE"
    mimeType: str | None = None
    fileSizeBytes: int | None = None


class CreateReportRequest(BaseModel):
    sourceChannel: str = Field(default="LIFF", max_length=30)
    reportText: str | None = None
    voiceText: str | None = None
    normalizedText: str | None = None
    reporterType: str | None = None
    label: str | None = None
    occurredAt: datetime | None = None
    location: ReportLocationInput | None = None
    attachments: list[ReportAttachmentInput] = []
    isAnonymous: bool = False


# ---- response ----

class CreateReportResponseData(BaseModel):
    reportId: str
    trackingCode: str
    incidentId: str | None = None
    isMerged: bool = False
    status: str
    candidateIncidentType: str | None = None


class ReportAttachmentOut(BaseModel):
    attachmentId: str
    fileKey: str
    fileUrl: str
    fileType: str
    mimeType: str | None = None


class ReportDetailResponseData(BaseModel):
    reportId: str
    trackingCode: str
    reportText: str | None = None
    voiceText: str | None = None
    normalizedText: str | None = None
    detectedLabels: list[str] = []
    candidateIncidentType: str | None = None
    linkedIncidentId: str | None = None
    attachments: list[ReportAttachmentOut] = []
    submittedAt: datetime | None = None
    status: str | None = None
    isAnonymous: bool = False


class ReportListItem(BaseModel):
    reportId: str
    trackingCode: str
    reportText: str | None = None
    candidateIncidentType: str | None = None
    status: str
    submittedAt: datetime | None = None


class ReportListResponseData(BaseModel):
    items: list[ReportListItem]
    pagination: PaginationMeta
