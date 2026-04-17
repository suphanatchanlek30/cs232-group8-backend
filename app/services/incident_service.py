"""Incident service — CRUD, actions, timeline, fusion/scoring explanation."""

import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import IncidentStatus
from app.models.incident import Incident
from app.models.incident_comment import IncidentComment
from app.models.incident_report import IncidentReport
from app.models.incident_status_history import IncidentStatusHistory
from app.models.report import Report
from app.models.report_attachment import ReportAttachment
from app.models.report_detected_label import ReportDetectedLabel
from app.models.unit import Unit
from app.models.user import User
from app.schemas.incident import (
    CommentResponseData,
    ConfidenceFactor,
    FusionExplanationResponseData,
    IncidentDetailResponseData,
    IncidentListItem,
    IncidentListResponseData,
    IncidentTimelineEntry,
    IncidentTimelineResponseData,
    ScoringExplanationResponseData,
)
from app.schemas.public import PaginationMeta
from app.schemas.report import ReportAttachmentOut, ReportDetailResponseData, ReportListItem, ReportListResponseData


# Valid state transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    IncidentStatus.NEW.value: [IncidentStatus.IN_REVIEW.value, IncidentStatus.IN_PROGRESS.value],
    IncidentStatus.IN_REVIEW.value: [IncidentStatus.IN_PROGRESS.value, IncidentStatus.RESOLVED.value],
    IncidentStatus.IN_PROGRESS.value: [IncidentStatus.RESOLVED.value, IncidentStatus.IN_REVIEW.value],
    IncidentStatus.RESOLVED.value: [IncidentStatus.CLOSED.value, IncidentStatus.IN_PROGRESS.value],
    IncidentStatus.CLOSED.value: [],
}

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def _get_incident_or_404(db: Session, incident_id: str) -> Incident:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident


def _get_unit_name(db: Session, unit_id) -> str | None:
    if unit_id is None:
        return None
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    return unit.name if unit else None


class IncidentService:
    # ==================================================== LIST
    @staticmethod
    def list_incidents(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        incident_status: str | None = None,
        severity: str | None = None,
        incident_type: str | None = None,
        assigned_unit_id: str | None = None,
        search: str | None = None,
        date_from=None,
        date_to=None,
        sort_by: str = "latestReportTime",
        sort_order: str = "desc",
    ) -> dict:
        query = db.query(Incident)

        if incident_status:
            query = query.filter(Incident.status == incident_status)
        if severity:
            query = query.filter(Incident.severity == severity)
        if incident_type:
            query = query.filter(Incident.incident_type == incident_type)
        if assigned_unit_id:
            query = query.filter(Incident.assigned_unit_id == assigned_unit_id)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Incident.incident_code.ilike(pattern)
                | Incident.summary_text.ilike(pattern)
                | Incident.location_name_snapshot.ilike(pattern)
            )
        if date_from:
            query = query.filter(Incident.first_report_time >= date_from)
        if date_to:
            query = query.filter(Incident.first_report_time <= date_to)

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size))

        # sorting
        sort_col = Incident.latest_report_time
        if sort_by == "firstReportTime":
            sort_col = Incident.first_report_time
        elif sort_by == "severity":
            sort_col = Incident.severity
        elif sort_by == "status":
            sort_col = Incident.status

        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        incidents = (
            query.offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = IncidentListResponseData(
            items=[
                IncidentListItem(
                    incidentId=str(inc.id),
                    incidentCode=inc.incident_code,
                    incidentType=inc.incident_type,
                    summary=inc.summary_text,
                    severity=inc.severity,
                    status=inc.status,
                    reportCount=inc.report_count,
                    assignedUnitName=_get_unit_name(db, inc.assigned_unit_id),
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

    # ==================================================== DETAIL
    @staticmethod
    def get_incident(db: Session, incident_id: str) -> dict:
        incident = _get_incident_or_404(db, incident_id)
        unit_name = _get_unit_name(db, incident.assigned_unit_id)

        data = IncidentDetailResponseData(
            incidentId=str(incident.id),
            incidentCode=incident.incident_code,
            incidentType=incident.incident_type,
            summary=incident.summary_text,
            severity=incident.severity,
            confidence=incident.confidence,
            confidenceScore=incident.confidence_score,
            status=incident.status,
            reportCount=incident.report_count,
            evidenceCount=incident.evidence_count,
            assignedUnitId=str(incident.assigned_unit_id) if incident.assigned_unit_id else None,
            assignedUnitName=unit_name,
            locationName=incident.location_name_snapshot,
            lat=float(incident.lat) if incident.lat is not None else None,
            lng=float(incident.lng) if incident.lng is not None else None,
            firstReportTime=incident.first_report_time,
            latestReportTime=incident.latest_report_time,
            resolvedAt=incident.resolved_at,
            resolutionSummary=incident.resolution_summary,
            createdAt=incident.created_at,
        )
        return data.model_dump()

    # =================================================== INCIDENT REPORTS
    @staticmethod
    def get_incident_reports(
        db: Session,
        incident_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        _get_incident_or_404(db, incident_id)

        query = db.query(Report).filter(Report.linked_incident_id == incident_id)
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

    # =================================================== INCIDENT TIMELINE
    @staticmethod
    def get_incident_timeline(db: Session, incident_id: str) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        history_rows = (
            db.query(IncidentStatusHistory)
            .filter(IncidentStatusHistory.incident_id == incident.id)
            .order_by(IncidentStatusHistory.changed_at)
            .all()
        )

        timeline = []
        for h in history_rows:
            actor_type = "SYSTEM"
            actor_name = None
            if h.changed_by_user_id:
                user = db.query(User).filter(User.id == h.changed_by_user_id).first()
                if user:
                    actor_type = user.role
                    actor_name = user.full_name

            if h.old_status is None:
                action_type = "INCIDENT_CREATED"
                description = "สร้าง incident ใหม่"
            else:
                action_type = "STATUS_CHANGED"
                description = f"เปลี่ยนสถานะจาก {h.old_status} เป็น {h.new_status}"
                if h.note:
                    description += f" — {h.note}"

            timeline.append(
                IncidentTimelineEntry(
                    actionType=action_type,
                    actorType=actor_type,
                    actorName=actor_name,
                    description=description,
                    changedAt=h.changed_at,
                )
            )

        data = IncidentTimelineResponseData(timeline=timeline)
        return data.model_dump()

    # =================================================== UPDATE STATUS
    @staticmethod
    def update_status(db: Session, incident_id: str, new_status: str, note: str | None, user: User) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        allowed = VALID_TRANSITIONS.get(incident.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition from {incident.status} to {new_status}",
            )

        old_status = incident.status
        incident.status = new_status
        if new_status == IncidentStatus.RESOLVED.value:
            incident.resolved_at = datetime.now(timezone.utc)

        history = IncidentStatusHistory(
            incident_id=incident.id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=user.id,
            note=note,
        )
        db.add(history)
        db.commit()
        db.refresh(incident)

        return {
            "incidentId": str(incident.id),
            "status": incident.status,
            "updatedAt": str(incident.updated_at) if hasattr(incident, "updated_at") else None,
        }

    # =================================================== ASSIGN UNIT
    @staticmethod
    def assign_unit(db: Session, incident_id: str, unit_id: str, note: str | None, user: User) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unit not found",
            )

        incident.assigned_unit_id = unit.id

        # record in timeline
        history = IncidentStatusHistory(
            incident_id=incident.id,
            old_status=incident.status,
            new_status=incident.status,
            changed_by_user_id=user.id,
            note=note or f"มอบหมายให้หน่วยงาน {unit.name}",
        )
        db.add(history)
        db.commit()
        db.refresh(incident)

        return {
            "incidentId": str(incident.id),
            "assignedUnitId": str(unit.id),
            "assignedUnitName": unit.name,
        }

    # =================================================== UPDATE PRIORITY
    @staticmethod
    def update_priority(db: Session, incident_id: str, severity: str, reason: str | None, user: User) -> dict:
        if severity not in VALID_SEVERITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}",
            )

        incident = _get_incident_or_404(db, incident_id)
        old_severity = incident.severity
        incident.severity = severity

        history = IncidentStatusHistory(
            incident_id=incident.id,
            old_status=incident.status,
            new_status=incident.status,
            changed_by_user_id=user.id,
            note=reason or f"ปรับระดับความรุนแรงจาก {old_severity} เป็น {severity}",
        )
        db.add(history)
        db.commit()
        db.refresh(incident)

        return {
            "incidentId": str(incident.id),
            "severity": incident.severity,
        }

    # =================================================== RESOLVE
    @staticmethod
    def resolve_incident(
        db: Session, incident_id: str,
        resolution_summary: str,
        resolved_at: datetime | None,
        user: User,
    ) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        if incident.status == IncidentStatus.RESOLVED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Incident already resolved",
            )

        old_status = incident.status
        incident.status = IncidentStatus.RESOLVED.value
        incident.resolved_at = resolved_at or datetime.now(timezone.utc)
        incident.resolution_summary = resolution_summary

        history = IncidentStatusHistory(
            incident_id=incident.id,
            old_status=old_status,
            new_status=IncidentStatus.RESOLVED.value,
            changed_by_user_id=user.id,
            note=f"ปิด incident: {resolution_summary}",
        )
        db.add(history)
        db.commit()
        db.refresh(incident)

        return {
            "incidentId": str(incident.id),
            "status": incident.status,
        }

    # =================================================== ADD COMMENT
    @staticmethod
    def add_comment(db: Session, incident_id: str, comment_text: str, user: User) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        if not comment_text or not comment_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment cannot be empty",
            )

        comment = IncidentComment(
            incident_id=incident.id,
            author_user_id=user.id,
            comment=comment_text,
            is_internal=True,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        data = CommentResponseData(
            commentId=str(comment.id),
            incidentId=str(incident.id),
            authorName=user.full_name,
            comment=comment.comment,
            isInternal=comment.is_internal,
            createdAt=comment.created_at,
        )
        return data.model_dump()

    # =================================================== FUSION EXPLANATION
    @staticmethod
    def get_fusion_explanation(db: Session, incident_id: str) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        # gather linked reports
        reports = (
            db.query(Report)
            .filter(Report.linked_incident_id == incident.id)
            .order_by(Report.submitted_at)
            .all()
        )

        merged_count = len(reports)

        # build explanation based on available data
        distance_meters = None
        time_diff_minutes = None
        type_similarity = merged_count > 1

        if merged_count >= 2:
            first = reports[0]
            last = reports[-1]
            if first.submitted_at and last.submitted_at:
                delta = (last.submitted_at - first.submitted_at).total_seconds() / 60
                time_diff_minutes = round(delta, 1)

            # simple distance approximation if coordinates are available
            if first.lat and first.lng and last.lat and last.lng:
                import math
                dlat = float(last.lat) - float(first.lat)
                dlng = float(last.lng) - float(first.lng)
                dist_deg = math.sqrt(dlat ** 2 + dlng ** 2)
                distance_meters = round(dist_deg * 111_000, 1)

        explanation = f"ระบบรวม {merged_count} รายงานเป็น incident เดียวกัน"
        if merged_count > 1:
            explanation += " เนื่องจากประเภทเหตุใกล้เคียงกัน"
            if distance_meters is not None:
                explanation += f" อยู่ในระยะ {distance_meters} เมตร"
            if time_diff_minutes is not None:
                explanation += f" และเกิดภายใน {time_diff_minutes} นาที"

        data = FusionExplanationResponseData(
            matchRules={
                "incidentTypeSimilarity": type_similarity,
                "distanceMeters": distance_meters,
                "timeDifferenceMinutes": time_diff_minutes,
            },
            mergedReports=merged_count,
            explanationText=explanation,
        )
        return data.model_dump()

    # =================================================== SCORING EXPLANATION
    @staticmethod
    def get_scoring_explanation(db: Session, incident_id: str) -> dict:
        incident = _get_incident_or_404(db, incident_id)

        # gather evidence factors
        reports = (
            db.query(Report)
            .filter(Report.linked_incident_id == incident.id)
            .all()
        )

        factors: list[ConfidenceFactor] = []

        # check for images
        has_image = False
        for r in reports:
            att_count = db.query(ReportAttachment).filter(
                ReportAttachment.report_id == r.id
            ).count()
            if att_count > 0:
                has_image = True
                break
        factors.append(ConfidenceFactor(factor="HAS_IMAGE", score=1 if has_image else 0))

        # check for matching labels
        has_matching_label = False
        for r in reports:
            label_count = db.query(ReportDetectedLabel).filter(
                ReportDetectedLabel.report_id == r.id
            ).count()
            if label_count > 0:
                has_matching_label = True
                break
        factors.append(ConfidenceFactor(factor="MATCHING_LABEL", score=1 if has_matching_label else 0))

        # multiple reports
        factors.append(ConfidenceFactor(
            factor="MULTIPLE_REPORTS",
            score=1 if incident.report_count > 1 else 0,
        ))

        # clear keyword (check if any report has text)
        has_text = any(r.report_text for r in reports)
        factors.append(ConfidenceFactor(factor="CLEAR_KEYWORD", score=1 if has_text else 0))

        severity_reason = f"Incident type: {incident.incident_type}, severity auto-assessed as {incident.severity}"

        data = ScoringExplanationResponseData(
            incidentType=incident.incident_type,
            severity=incident.severity,
            severityReason=severity_reason,
            confidence=incident.confidence,
            confidenceFactors=factors,
        )
        return data.model_dump()
