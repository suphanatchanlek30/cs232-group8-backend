"""Analytics service — KPI, distribution, hotspot, peak-time, fusion stats, status overview."""

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.report import Report


class AnalyticsService:

    @staticmethod
    def _between_or_all(query, column, date_from, date_to):
        if date_from and date_to:
            return query.filter(column.between(date_from, date_to))
        if date_from:
            return query.filter(column >= date_from)
        if date_to:
            return query.filter(column <= date_to)
        return query

    @staticmethod
    def get_kpi_summary(db: Session, date_from, date_to, unit_id=None):
        total_reports = (
            AnalyticsService._between_or_all(
                db.query(func.count(Report.id)), Report.submitted_at, date_from, date_to,
            )
            .scalar()
        ) or 0

        inc_query = AnalyticsService._between_or_all(
            db.query(Incident), Incident.first_report_time, date_from, date_to,
        )
        if unit_id:
            inc_query = inc_query.filter(Incident.assigned_unit_id == unit_id)

        total_incidents = inc_query.count()
        resolved_count = inc_query.filter(Incident.status == "RESOLVED").count()

        merged = max(0, total_reports - total_incidents)

        return {
            "totalReports": total_reports,
            "totalIncidents": total_incidents,
            "fusionRate": round((merged / total_reports * 100), 2) if total_reports else 0,
            "avgResponseMinutes": 0,  # placeholder — requires actual response time tracking
            "resolvedRate": round((resolved_count / total_incidents * 100), 2) if total_incidents else 0,
        }

    @staticmethod
    def get_incident_type_distribution(db: Session, date_from, date_to):
        query = db.query(
            Incident.incident_type.label("incidentType"),
            func.count().label("count"),
        )
        rows = (
            AnalyticsService._between_or_all(
                query, Incident.first_report_time, date_from, date_to,
            )
            .group_by(Incident.incident_type)
            .all()
        )
        return [{"incidentType": r.incidentType, "count": r.count} for r in rows]

    @staticmethod
    def get_hotspots(db: Session, date_from, date_to, limit):
        query = db.query(
            Incident.location_name_snapshot.label("locationName"),
            func.count().label("incidentCount"),
            Incident.lat,
            Incident.lng,
        ).filter(Incident.location_name_snapshot.isnot(None))

        rows = (
            AnalyticsService._between_or_all(
                query, Incident.first_report_time, date_from, date_to,
            )
            .group_by(Incident.location_name_snapshot, Incident.lat, Incident.lng)
            .order_by(func.count().desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "locationName": r.locationName,
                "incidentCount": r.incidentCount,
                "lat": float(r.lat) if r.lat else None,
                "lng": float(r.lng) if r.lng else None,
            }
            for r in rows
        ]

    @staticmethod
    def get_peak_time(db: Session, date_from, date_to, group_by: str = "hour"):
        if group_by == "day":
            query = db.query(
                func.extract("dow", Report.submitted_at).label("day"),
                func.count().label("count"),
            )
            rows = (
                AnalyticsService._between_or_all(query, Report.submitted_at, date_from, date_to)
                .group_by("day")
                .order_by("day")
                .all()
            )
            return [{"day": int(r.day), "count": r.count} for r in rows]

        query = db.query(
            func.extract("hour", Report.submitted_at).label("hour"),
            func.count().label("count"),
        )
        rows = (
            AnalyticsService._between_or_all(query, Report.submitted_at, date_from, date_to)
            .group_by("hour")
            .order_by("hour")
            .all()
        )
        return [{"hour": int(r.hour), "count": r.count} for r in rows]

    @staticmethod
    def get_fusion_stats(db: Session, date_from, date_to):
        total_reports = (
            AnalyticsService._between_or_all(
                db.query(func.count(Report.id)), Report.submitted_at, date_from, date_to,
            )
            .scalar()
        ) or 0

        total_incidents = (
            AnalyticsService._between_or_all(
                db.query(func.count(Incident.id)), Incident.first_report_time, date_from, date_to,
            )
            .scalar()
        ) or 0

        merged = max(0, total_reports - total_incidents)

        return {
            "totalReports": total_reports,
            "totalIncidents": total_incidents,
            "mergedReports": merged,
            "fusionRate": round((merged / total_reports * 100), 2) if total_reports else 0,
            "avgReportsPerIncident": round(total_reports / total_incidents, 2) if total_incidents else 0,
        }

    @staticmethod
    def get_status_overview(db: Session, date_from, date_to):
        query = db.query(
            Incident.status,
            func.count().label("count"),
        )
        rows = (
            AnalyticsService._between_or_all(
                query, Incident.first_report_time, date_from, date_to,
            )
            .group_by(Incident.status)
            .all()
        )
        return [{"status": r.status, "count": r.count} for r in rows]
