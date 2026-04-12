import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin, utc_now


class IncidentReport(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "incident_reports"
    __table_args__ = (UniqueConstraint("incident_id", "report_id", name="uq_incident_report"),)

    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    is_primary_report: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    merged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)