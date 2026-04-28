import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import IncidentLabel, IncidentStatus, ReportStatus
from app.models.incident import Incident
from app.models.incident_report import IncidentReport
from app.models.incident_status_history import IncidentStatusHistory
from app.models.location import Location
from app.models.report import Report
from app.models.report_attachment import ReportAttachment
from app.models.report_detected_label import ReportDetectedLabel
from app.models.routing_rule import RoutingRule
from app.models.user import User
from app.schemas.public import PaginationMeta
from app.schemas.report import (
    CreateReportResponseData,
    ReportAttachmentOut,
    ReportDetailResponseData,
    ReportListItem,
    ReportListResponseData,
)


def _generate_tracking_code() -> str:
    """Generate a tracking code like TP-20260412-XXXX."""
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:4].upper()
    return f"TP-{date_part}-{random_part}"


def _find_or_create_incident(
    db: Session,
    report: Report,
    label: str | None,
) -> Incident | None:
    """
    Simple incident-matching logic:
    - If the report has a label and there is an existing NEW/IN_REVIEW incident
      with the same incident_type, merge into it.
    - Otherwise create a new incident.
    Returns the incident (existing or new).
    """
    if not label:
        return None

    now = datetime.now(timezone.utc)

    # try to find an open incident with the same type
    existing = (
        db.query(Incident)
        .filter(
            Incident.incident_type == label,
            Incident.status.in_([IncidentStatus.NEW.value, IncidentStatus.IN_REVIEW.value]),
        )
        .first()
    )

    if existing:
        existing.report_count += 1
        existing.latest_report_time = now
        return existing

    # create new incident
    incident_code = f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    # try to find assigned unit from routing rules
    assigned_unit_id = None
    rule = (
        db.query(RoutingRule)
        .filter(RoutingRule.incident_type == label, RoutingRule.is_active.is_(True))
        .order_by(RoutingRule.priority)
        .first()
    )
    if rule:
        assigned_unit_id = rule.assigned_unit_id

    incident = Incident(
        incident_code=incident_code,
        incident_type=label,
        severity="LOW",
        confidence="LOW",
        confidence_score=50,
        status=IncidentStatus.NEW.value,
        first_report_time=now,
        latest_report_time=now,
        report_count=1,
        evidence_count=0,
        assigned_unit_id=assigned_unit_id,
        lat=report.lat,
        lng=report.lng,
        location_id=report.location_id,
        location_name_snapshot=report.location_name_snapshot,
        location_note=report.location_note,
        created_by_system=True,
    )
    db.add(incident)
    db.flush()

    # initial status history
    history = IncidentStatusHistory(
        incident_id=incident.id,
        old_status=None,
        new_status=IncidentStatus.NEW.value,
        changed_by_user_id=None,
        note="Incident created from report",
    )
    db.add(history)

    return incident


class ReportService:
    # ---------------------------------------------------------------- create
    @staticmethod
    def create_report(db: Session, user: User, payload) -> dict:
        tracking_code = _generate_tracking_code()

        # resolve location
        location_id = None
        location_name_snapshot = None
        lat = None
        lng = None

        if payload.location:
            lat = payload.location.lat
            lng = payload.location.lng
            location_name_snapshot = payload.location.locationName

            if payload.location.locationId:
                loc = db.query(Location).filter(
                    Location.id == payload.location.locationId
                ).first()
                if loc:
                    location_id = loc.id
                    location_name_snapshot = location_name_snapshot or loc.location_name

        report = Report(
            tracking_code=tracking_code,
            reporter_user_id=user.id,
            source_channel=payload.sourceChannel,
            report_text=payload.reportText,
            voice_text=payload.voiceText,
            normalized_text=payload.normalizedText,
            user_selected_label=payload.label,
            candidate_incident_type=payload.label,
            occurred_at=payload.occurredAt,
            location_id=location_id,
            location_name_snapshot=location_name_snapshot,
            lat=lat,
            lng=lng,
            report_status=ReportStatus.SUBMITTED.value,
            is_anonymous=payload.isAnonymous,
        )
        db.add(report)
        db.flush()

        # update reporter_type on User if provided
        if payload.reporterType and user.reporter_type != payload.reporterType:
            user.reporter_type = payload.reporterType

        # save attachments
        for att in payload.attachments:
            db.add(ReportAttachment(
                report_id=report.id,
                file_key=att.fileKey,
                file_url=att.fileUrl,
                file_type=att.fileType,
                mime_type=att.mimeType,
                file_size_bytes=att.fileSizeBytes,
            ))

        # save user-selected label as detected label
        if payload.label:
            db.add(ReportDetectedLabel(
                report_id=report.id,
                label_name=payload.label,
                confidence=1.0,
                source="USER",
            ))

        # incident matching
        incident = _find_or_create_incident(db, report, payload.label)
        is_merged = False
        incident_id_str = None

        if incident:
            report.linked_incident_id = incident.id
            report.report_status = ReportStatus.LINKED_TO_INCIDENT.value

            link = IncidentReport(
                incident_id=incident.id,
                report_id=report.id,
                is_primary_report=(incident.report_count == 1),
            )
            db.add(link)
            is_merged = incident.report_count > 1
            incident_id_str = str(incident.id)

        db.commit()
        db.refresh(report)

        data = CreateReportResponseData(
            reportId=str(report.id),
            trackingCode=report.tracking_code,
            incidentId=incident_id_str,
            isMerged=is_merged,
            status=report.report_status,
            candidateIncidentType=report.candidate_incident_type,
        )
        return data.model_dump()

    # --------------------------------------------------------- create multipart
    @staticmethod
    def create_report_multipart(
        db: Session,
        user: User,
        report_text: str | None,
        voice_text: str | None,
        label: str | None,
        occurred_at: datetime | None,
        location_name: str | None,
        location_note: str | None,
        lat: float | None,
        lng: float | None,
        attachments_data: list[dict],
    ) -> dict:
        """Simplified multipart endpoint — stores images directly to S3."""
        tracking_code = _generate_tracking_code()

        report = Report(
            tracking_code=tracking_code,
            reporter_user_id=user.id,
            source_channel="LIFF",
            report_text=report_text,
            voice_text=voice_text,
            normalized_text=report_text,
            user_selected_label=label,
            candidate_incident_type=label,
            occurred_at=occurred_at,
            location_name_snapshot=location_name,
            location_note=location_note,
            lat=lat,
            lng=lng,
            report_status=ReportStatus.SUBMITTED.value,
        )
        db.add(report)
        db.flush()

        for data in attachments_data:
            db.add(ReportAttachment(
                report_id=report.id,
                file_key=data["file_key"],
                file_url=data["file_url"],
                file_type=data["file_type"],
                mime_type=data.get("mime_type"),
                file_size_bytes=data.get("file_size_bytes"),
            ))

        if label:
            db.add(ReportDetectedLabel(
                report_id=report.id,
                label_name=label,
                confidence=1.0,
                source="USER",
            ))

        incident = _find_or_create_incident(db, report, label)
        is_merged = False
        incident_id_str = None

        if incident:
            report.linked_incident_id = incident.id
            report.report_status = ReportStatus.LINKED_TO_INCIDENT.value
            link = IncidentReport(
                incident_id=incident.id,
                report_id=report.id,
                is_primary_report=(incident.report_count == 1),
            )
            db.add(link)
            is_merged = incident.report_count > 1
            incident_id_str = str(incident.id)

        db.commit()
        db.refresh(report)

        data = CreateReportResponseData(
            reportId=str(report.id),
            trackingCode=report.tracking_code,
            incidentId=incident_id_str,
            isMerged=is_merged,
            status=report.report_status,
            candidateIncidentType=report.candidate_incident_type,
        )
        return data.model_dump()

    # ------------------------------------------------------------ get detail
    @staticmethod
    def get_report(db: Session, report_id: str, user: User) -> dict:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        # access control: reporter owner OR staff/admin
        is_owner = report.reporter_user_id == user.id
        is_staff = user.role in ("STAFF", "ADMIN")
        if not is_owner and not is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        attachments = (
            db.query(ReportAttachment)
            .filter(ReportAttachment.report_id == report.id)
            .all()
        )
        labels = (
            db.query(ReportDetectedLabel)
            .filter(ReportDetectedLabel.report_id == report.id)
            .all()
        )

        data = ReportDetailResponseData(
            reportId=str(report.id),
            trackingCode=report.tracking_code,
            reportText=report.report_text,
            voiceText=report.voice_text,
            normalizedText=report.normalized_text,
            detectedLabels=[lb.label_name for lb in labels],
            candidateIncidentType=report.candidate_incident_type,
            linkedIncidentId=str(report.linked_incident_id) if report.linked_incident_id else None,
            attachments=[
                ReportAttachmentOut(
                    attachmentId=str(a.id),
                    fileKey=a.file_key,
                    fileUrl=a.file_url,
                    fileType=a.file_type,
                    mimeType=a.mime_type,
                )
                for a in attachments
            ],
            submittedAt=report.submitted_at,
            status=report.report_status,
            isAnonymous=report.is_anonymous,
        )
        return data.model_dump()

    @staticmethod
    def get_report_images(db: Session, report_id: str, user: User) -> list[str]:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found",
            )

        # access control: reporter owner OR staff/admin
        is_owner = report.reporter_user_id == user.id
        is_staff = user.role in ("STAFF", "ADMIN")
        if not is_owner and not is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        attachments = (
            db.query(ReportAttachment)
            .filter(ReportAttachment.report_id == report.id)
            .filter(ReportAttachment.file_type == "IMAGE")
            .all()
        )
        return [a.file_url for a in attachments]

    # ------------------------------------------------------------ my reports
    @staticmethod
    def get_my_reports(
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 20,
        report_status: str | None = None,
    ) -> dict:
        query = db.query(Report).filter(Report.reporter_user_id == user.id)

        if report_status:
            query = query.filter(Report.report_status == report_status)

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size))

        items = (
            query.order_by(Report.submitted_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = ReportListResponseData(
            items=[
                ReportListItem(
                    reportId=str(r.id),
                    trackingCode=r.tracking_code,
                    reportText=r.report_text,
                    candidateIncidentType=r.candidate_incident_type,
                    status=r.report_status,
                    submittedAt=r.submitted_at,
                )
                for r in items
            ],
            pagination=PaginationMeta(
                page=page,
                pageSize=page_size,
                totalItems=total_items,
                totalPages=total_pages,
            ),
        )
        return data.model_dump()
