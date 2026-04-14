import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.incident_report import IncidentReport
from app.models.incident_status_history import IncidentStatusHistory
from app.models.report import Report
from app.models.unit import Unit
from app.models.user import User
from app.schemas.public import PaginationMeta
from app.schemas.tracking import (
    MyIncidentItem,
    MyIncidentListResponseData,
    TimelineEntry,
    TrackingResponseData,
    TrackingTimelineResponseData,
)


class TrackingService:
    # ------------------------------------------------------- track by code
    @staticmethod
    def track_by_code(db: Session, tracking_code: str) -> dict:
        report = (
            db.query(Report)
            .filter(Report.tracking_code == tracking_code)
            .first()
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        incident_id_str = None
        incident_type = None
        incident_status = report.report_status
        severity = None
        assigned_unit_name = None
        latest_updated = report.submitted_at

        if report.linked_incident_id:
            incident = db.query(Incident).filter(Incident.id == report.linked_incident_id).first()
            if incident:
                incident_id_str = str(incident.id)
                incident_type = incident.incident_type
                incident_status = incident.status
                severity = incident.severity
                latest_updated = incident.latest_report_time

                if incident.assigned_unit_id:
                    unit = db.query(Unit).filter(Unit.id == incident.assigned_unit_id).first()
                    if unit:
                        assigned_unit_name = unit.name

        data = TrackingResponseData(
            trackingCode=report.tracking_code,
            reportId=str(report.id),
            incidentId=incident_id_str,
            incidentType=incident_type or report.candidate_incident_type,
            status=incident_status,
            severity=severity,
            assignedUnit=assigned_unit_name,
            latestUpdatedAt=latest_updated,
        )
        return data.model_dump()

    # -------------------------------------------------- timeline by code
    @staticmethod
    def get_timeline(db: Session, tracking_code: str) -> dict:
        report = (
            db.query(Report)
            .filter(Report.tracking_code == tracking_code)
            .first()
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        timeline_entries: list[TimelineEntry] = []

        # always include SUBMITTED as first entry
        timeline_entries.append(
            TimelineEntry(
                status="SUBMITTED",
                changedAt=report.submitted_at,
                note="Report submitted",
            )
        )

        # if linked to an incident, pull status history from it
        if report.linked_incident_id:
            history_rows = (
                db.query(IncidentStatusHistory)
                .filter(IncidentStatusHistory.incident_id == report.linked_incident_id)
                .order_by(IncidentStatusHistory.changed_at)
                .all()
            )
            for h in history_rows:
                # skip the initial NEW if it would duplicate SUBMITTED
                if h.new_status == "NEW" and h.old_status is None:
                    continue
                timeline_entries.append(
                    TimelineEntry(
                        status=h.new_status,
                        changedAt=h.changed_at,
                        note=h.note,
                    )
                )

        data = TrackingTimelineResponseData(timeline=timeline_entries)
        return data.model_dump()

    # -------------------------------------------------- my incidents
    @staticmethod
    def get_my_incidents(
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        # find all incident IDs linked to user's reports
        subq = (
            db.query(Report.linked_incident_id)
            .filter(
                Report.reporter_user_id == user.id,
                Report.linked_incident_id.isnot(None),
            )
            .distinct()
            .subquery()
        )

        query = db.query(Incident).filter(Incident.id.in_(subq))

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size))

        incidents = (
            query.order_by(Incident.latest_report_time.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = MyIncidentListResponseData(
            items=[
                MyIncidentItem(
                    incidentId=str(inc.id),
                    incidentCode=inc.incident_code,
                    incidentType=inc.incident_type,
                    summary=inc.summary_text,
                    severity=inc.severity,
                    status=inc.status,
                    reportCount=inc.report_count,
                    firstReportTime=inc.first_report_time,
                    latestReportTime=inc.latest_report_time,
                )
                for inc in incidents
            ],
            pagination=PaginationMeta(
                page=page,
                pageSize=page_size,
                totalItems=total_items,
                totalPages=total_pages,
            ),
        )
        return data.model_dump()
