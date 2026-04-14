from pydantic import BaseModel


class SystemInfoResponseData(BaseModel):
    systemName: str
    projectNameEn: str
    allowReportSubmission: bool
    version: str


class ReportOptionsResponseData(BaseModel):
    incidentLabels: list[str]
    reporterTypes: list[str]


class LocationItem(BaseModel):
    locationId: str
    locationName: str
    buildingCode: str | None = None
    campusZone: str | None = None
    lat: float | None = None
    lng: float | None = None


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    totalItems: int
    totalPages: int


class LocationListResponseData(BaseModel):
    items: list[LocationItem]
    pagination: PaginationMeta
