from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff
from app.db.session import get_db
from app.schemas.auth import RefreshTokenRequest, TokenRefreshResponseData
from app.schemas.common import ApiResponse
from app.schemas.staff_auth import StaffLoginRequest
from app.services.staff_auth_service import StaffAuthService

router = APIRouter()


@router.post("/login", response_model=ApiResponse)
def staff_login(
    payload: StaffLoginRequest,
    db: Session = Depends(get_db),
):
    data = StaffAuthService.login(db, payload.email, payload.password)
    return ApiResponse(
        success=True,
        message="เข้าสู่ระบบสำเร็จ",
        data=data,
    )


@router.post("/refresh", response_model=ApiResponse)
def staff_refresh(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    data = StaffAuthService.refresh_access_token(db, payload.refreshToken)
    return ApiResponse(
        success=True,
        message="ต่ออายุ token สำเร็จ",
        data=TokenRefreshResponseData(**data).model_dump(),
    )


@router.post("/logout", response_model=ApiResponse)
def staff_logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    StaffAuthService.logout(db, payload.refreshToken)
    return ApiResponse(
        success=True,
        message="ออกจากระบบสำเร็จ",
        data=None,
    )


@router.get("/me", response_model=ApiResponse)
def staff_me(
    user=Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    data = StaffAuthService.get_me(db, user)
    return ApiResponse(
        success=True,
        message="ดึงข้อมูลผู้ใช้สำเร็จ",
        data=data,
    )
