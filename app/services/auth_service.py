from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import AuthProvider, ReporterType, UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import ExchangeTokenResponseData, UserResponseData
from app.services.line_service import LineService


class AuthService:
    @staticmethod
    def exchange_liff_token(db: Session, payload) -> dict:
        line_payload = LineService.verify_id_token(payload.idToken)

        line_user_id = line_payload.get("sub")
        if not line_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload",
            )

        line_name = payload.displayName or line_payload.get("name") or "LINE User"
        picture_url = payload.pictureUrl or line_payload.get("picture")

        user = db.query(User).filter(User.line_user_id == line_user_id).first()

        if not user:
            user = User(
                role=UserRole.REPORTER.value,
                auth_provider=AuthProvider.LIFF.value,
                line_user_id=line_user_id,
                line_display_name=line_name,
                full_name=line_name,
                profile_image_url=picture_url,
                reporter_type=ReporterType.STUDENT.value,
                is_active=True,
            )
            db.add(user)
            db.flush()
        else:
            user.line_display_name = line_name
            user.full_name = line_name
            user.profile_image_url = picture_url

        user.last_login_at = datetime.now(timezone.utc)

        access_token = create_access_token(
            subject=str(user.id),
            extra_data={
                "role": user.role,
                "auth_provider": user.auth_provider,
            },
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            extra_data={
                "role": user.role,
                "auth_provider": user.auth_provider,
            },
        )

        refresh_token_row = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(refresh_token_row)
        db.commit()
        db.refresh(user)

        response = ExchangeTokenResponseData(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=UserResponseData(
                userId=str(user.id),
                lineUserId=user.line_user_id,
                fullName=user.full_name,
                role=user.role,
            ),
        )
        return response.model_dump()

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict:
        payload = decode_refresh_token(refresh_token)

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
            )

        token_hash = hash_token(refresh_token)
        token_row = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
            )
            .first()
        )

        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if token_row.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Refresh token revoked",
            )

        if token_row.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        access_token = create_access_token(
            subject=str(user.id),
            extra_data={
                "role": user.role,
                "auth_provider": user.auth_provider,
            },
        )
        return {"accessToken": access_token}

    @staticmethod
    def logout(db: Session, refresh_token: str) -> None:
        payload = decode_refresh_token(refresh_token)

        if payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload",
            )

        user_id = payload.get("sub")
        token_hash = hash_token(refresh_token)

        token_row = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
            )
            .first()
        )

        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        token_row.revoked_at = datetime.now(timezone.utc)
        db.commit()