from datetime import datetime

from pydantic import BaseModel

from app.schemas.public import PaginationMeta


# ---- Dashboard / Incident List ----

class DashboardSummaryResponseData(BaseModel):
    totalIncidents: int
    newCount: int
    inReviewCount: int
    inProgressCount: int
    resolvedCount: int
    highSeverityCount: int


class IncidentListItem(BaseModel):
    incidentId: str
    incidentCode: str
    incidentType: str
    summary: str | None = None
    severity: str
    status: str
    reportCount: int
    assignedUnitName: str | None = None
    locationName: str | None = None
    locationNote: str | None = None
    firstReportTime: datetime
    latestReportTime: datetime


class IncidentListResponseData(BaseModel):
    items: list[IncidentListItem]
    pagination: PaginationMeta


# ---- Incident Detail ----

class IncidentDetailResponseData(BaseModel):
    incidentId: str
    incidentCode: str
    incidentType: str
    summary: str | None = None
    severity: str
    confidence: str
    confidenceScore: int
    status: str
    reportCount: int
    evidenceCount: int
    assignedUnitId: str | None = None
    assignedUnitName: str | None = None
    locationName: str | None = None
    locationNote: str | None = None
    lat: float | None = None
    lng: float | None = None
    firstReportTime: datetime
    latestReportTime: datetime
    resolvedAt: datetime | None = None
    resolutionSummary: str | None = None
    createdAt: datetime | None = None


# ---- Incident Timeline ----

class IncidentTimelineEntry(BaseModel):
    actionType: str
    actorType: str
    actorName: str | None = None
    description: str | None = None
    changedAt: datetime


class IncidentTimelineResponseData(BaseModel):
    timeline: list[IncidentTimelineEntry]


# ---- Incident Actions ----

class UpdateStatusRequest(BaseModel):
    status: str
    note: str | None = None


class AssignUnitRequest(BaseModel):
    assignedUnitId: str
    note: str | None = None


class UpdatePriorityRequest(BaseModel):
    severity: str
    reason: str | None = None


class ResolveIncidentRequest(BaseModel):
    resolutionSummary: str
    resolvedAt: datetime | None = None


class AddCommentRequest(BaseModel):
    comment: str


class CommentResponseData(BaseModel):
    commentId: str
    incidentId: str
    authorName: str
    comment: str
    isInternal: bool
    createdAt: datetime


# ---- Fusion / Intelligence ----

class FusionExplanationResponseData(BaseModel):
    matchRules: dict
    mergedReports: int
    explanationText: str


class ConfidenceFactor(BaseModel):
    factor: str
    score: int


class ScoringExplanationResponseData(BaseModel):
    incidentType: str
    severity: str
    severityReason: str
    confidence: str
    confidenceFactors: list[ConfidenceFactor]
