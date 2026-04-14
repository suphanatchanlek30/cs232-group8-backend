from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.unit import Unit
from app.models.user import User
from app.schemas.staff_auth import (
    StaffLoginResponseData,
    StaffMeResponseData,
    StaffUnitResponseData,
    StaffUserResponseData,
)

# -------------------------------------------------------------------
# Permission map: role → list of permission strings
# Extend this map as the system grows.
# -------------------------------------------------------------------
ROLE_PERMISSIONS: dict[str, list[str]] = {
    UserRole.STAFF.value: [
        "incident.read",
        "incident.update_status",
    ],
    UserRole.ADMIN.value: [
        "incident.read",
        "incident.update_status",
        "incident.delete",
        "user.manage",
        "unit.manage",
        "routing_rule.manage",
    ],
}


def _build_unit_data(db: Session, user: User) -> StaffUnitResponseData | None:
    """Return unit info for a staff user, or None if unassigned."""
    if user.unit_id is None:
        return None
    unit = db.query(Unit).filter(Unit.id == user.unit_id).first()
    if unit is None:
        return None
    return StaffUnitResponseData(unitId=str(unit.id), name=unit.name)


class StaffAuthService:
    # ------------------------------------------------------------------ login
    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive account",
            )

        if user.role not in (UserRole.STAFF.value, UserRole.ADMIN.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only staff or admin can use this endpoint",
            )

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

        unit_data = _build_unit_data(db, user)

        response = StaffLoginResponseData(
            accessToken=access_token,
            refreshToken=refresh_token,
            user=StaffUserResponseData(
                userId=str(user.id),
                fullName=user.full_name,
                email=user.email or "",
                role=user.role,
                unit=unit_data,
            ),
        )
        return response.model_dump()

    # -------------------------------------------------------------- refresh
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

        user = (
            db.query(User)
            .filter(
                User.id == user_id,
                User.is_active.is_(True),
                User.role.in_([UserRole.STAFF.value, UserRole.ADMIN.value]),
            )
            .first()
        )
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

    # --------------------------------------------------------------- logout
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

    # ------------------------------------------------------------------- me
    @staticmethod
    def get_me(db: Session, user: User) -> dict:
        unit_data = _build_unit_data(db, user)
        permissions = ROLE_PERMISSIONS.get(user.role, [])

        response = StaffMeResponseData(
            userId=str(user.id),
            fullName=user.full_name,
            email=user.email or "",
            role=user.role,
            unit=unit_data,
            permissions=permissions,
        )
        return response.model_dump()
