import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Incident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "incidents"

    incident_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assigned_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="NEW", nullable=False)

    first_report_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latest_report_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    report_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    location_name_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    hotspot_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)