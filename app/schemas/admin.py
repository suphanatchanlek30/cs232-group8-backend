from pydantic import BaseModel, EmailStr, Field

from app.schemas.public import PaginationMeta


# ---- Units ----

class CreateUnitRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    email: EmailStr | None = None
    description: str | None = None


class UnitItem(BaseModel):
    unitId: str
    code: str
    name: str
    contactEmail: str | None = None
    description: str | None = None
    isActive: bool


class UnitListResponseData(BaseModel):
    items: list[UnitItem]
    pagination: PaginationMeta


# ---- Locations ----

class CreateLocationRequest(BaseModel):
    locationName: str = Field(..., min_length=1, max_length=255)
    buildingCode: str | None = None
    campusZone: str | None = None
    lat: float | None = None
    lng: float | None = None


class LocationCreatedResponseData(BaseModel):
    locationId: str
    locationName: str
    buildingCode: str | None = None
    lat: float | None = None
    lng: float | None = None


# ---- Routing Rules ----

class CreateRoutingRuleRequest(BaseModel):
    incidentType: str = Field(..., min_length=1, max_length=50)
    severity: str | None = None
    assignedUnitId: str = Field(..., min_length=1)
    priority: int = 1


class RoutingRuleItem(BaseModel):
    ruleId: str
    incidentType: str
    severity: str | None = None
    assignedUnitId: str
    assignedUnitName: str | None = None
    priority: int
    isActive: bool


class RoutingRuleListResponseData(BaseModel):
    items: list[RoutingRuleItem]


# ---- Staff Users ----

class CreateStaffUserRequest(BaseModel):
    fullName: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    unitId: str | None = None
    role: str = "STAFF"


class StaffUserCreatedResponseData(BaseModel):
    userId: str
    fullName: str
    email: str
    role: str
    unitId: str | None = None
