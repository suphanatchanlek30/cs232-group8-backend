import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    role: Mapped[str] = mapped_column(String(30), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(30), nullable=False)

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    line_user_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    line_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    reporter_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)