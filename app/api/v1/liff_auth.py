from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_reporter
from app.db.session import get_db
from app.schemas.auth import (
    LiffExchangeRequest,
    RefreshTokenRequest,
    TokenRefreshResponseData,
    UserMeResponseData,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/exchange", response_model=ApiResponse)
def exchange_liff_token(
    payload: LiffExchangeRequest,
    db: Session = Depends(get_db),
):
    data = AuthService.exchange_liff_token(db, payload)
    return ApiResponse(
        success=True,
        message="เข้าสู่ระบบผ่าน LINE สำเร็จ",
        data=data,
    )


@router.post("/refresh", response_model=ApiResponse)
def refresh_liff_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    data = AuthService.refresh_access_token(db, payload.refreshToken)
    return ApiResponse(
        success=True,
        message="ต่ออายุ token สำเร็จ",
        data=TokenRefreshResponseData(**data).model_dump(),
    )


@router.post("/logout", response_model=ApiResponse)
def logout_liff(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    AuthService.logout(db, payload.refreshToken)
    return ApiResponse(
        success=True,
        message="ออกจากระบบสำเร็จ",
        data=None,
    )


@router.get("/me", response_model=ApiResponse)
def get_me(user=Depends(get_current_reporter)):
    data = UserMeResponseData(
        userId=str(user.id),
        fullName=user.full_name,
        lineDisplayName=user.line_display_name,
        role=user.role,
        reporterType=user.reporter_type,
    )
    return ApiResponse(
        success=True,
        message="ดึงข้อมูลผู้ใช้สำเร็จ",
        data=data.model_dump(),
    )