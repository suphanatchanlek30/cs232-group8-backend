from pydantic import BaseModel, Field, EmailStr


class StaffLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class StaffUnitResponseData(BaseModel):
    unitId: str
    name: str


class StaffUserResponseData(BaseModel):
    userId: str
    fullName: str
    email: str
    role: str
    unit: StaffUnitResponseData | None = None


class StaffLoginResponseData(BaseModel):
    accessToken: str
    refreshToken: str
    user: StaffUserResponseData


class StaffMeResponseData(BaseModel):
    userId: str
    fullName: str
    email: str
    role: str
    unit: StaffUnitResponseData | None = None
    permissions: list[str] = []
