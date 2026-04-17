"""Dashboard service — provides KPI summary for the dashboard page."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import IncidentStatus
from app.models.incident import Incident
from app.schemas.incident import DashboardSummaryResponseData


class DashboardService:
    @staticmethod
    def get_summary(
        db: Session,
        date_from=None,
        date_to=None,
        unit_id: str | None = None,
    ) -> dict:
        query = db.query(Incident)

        if date_from:
            query = query.filter(Incident.first_report_time >= date_from)
        if date_to:
            query = query.filter(Incident.first_report_time <= date_to)
        if unit_id:
            query = query.filter(Incident.assigned_unit_id == unit_id)

        total = query.count()

        new_count = query.filter(
            Incident.status == IncidentStatus.NEW.value
        ).count()
        in_review_count = query.filter(
            Incident.status == IncidentStatus.IN_REVIEW.value
        ).count()
        in_progress_count = query.filter(
            Incident.status == IncidentStatus.IN_PROGRESS.value
        ).count()
        resolved_count = query.filter(
            Incident.status == IncidentStatus.RESOLVED.value
        ).count()
        high_severity_count = query.filter(
            Incident.severity == "HIGH"
        ).count()

        data = DashboardSummaryResponseData(
            totalIncidents=total,
            newCount=new_count,
            inReviewCount=in_review_count,
            inProgressCount=in_progress_count,
            resolvedCount=resolved_count,
            highSeverityCount=high_severity_count,
        )
        return data.model_dump()
