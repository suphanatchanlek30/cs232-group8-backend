from pydantic import BaseModel, Field


class LiffExchangeRequest(BaseModel):
    idToken: str = Field(..., min_length=1)
    displayName: str | None = None
    pictureUrl: str | None = None


class RefreshTokenRequest(BaseModel):
    refreshToken: str = Field(..., min_length=1)


class UserResponseData(BaseModel):
    userId: str
    lineUserId: str | None = None
    fullName: str
    role: str


class ExchangeTokenResponseData(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserResponseData


class TokenRefreshResponseData(BaseModel):
    accessToken: str


class UserMeResponseData(BaseModel):
    userId: str
    fullName: str
    lineDisplayName: str | None = None
    role: str
    reporterType: str | None = None