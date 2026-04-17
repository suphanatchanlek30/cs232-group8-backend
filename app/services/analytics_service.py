from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models.report import Report


class AnalyticsService:

    @staticmethod
    def get_kpi_summary(db: Session, date_from, date_to, unit_id=None):
        query = db.query(
            func.count().label("totalReports"),
            func.count(distinct(Report.incident_id)).label("totalIncidents"),
            func.avg(
                func.extract("epoch", Report.resolved_at - Report.created_at) / 60
            ).label("avgResponseMinutes"),
            func.sum(
                func.case((Report.status == "RESOLVED", 1), else_=0)
            ).label("resolvedCount")
        ).filter(
            Report.created_at.between(date_from, date_to)
        )

        if unit_id:
            query = query.filter(Report.unit_id == unit_id)

        result = query.first()

        total_reports = result.totalReports or 0
        total_incidents = result.totalIncidents or 0
        merged = total_reports - total_incidents

        return {
            "totalReports": total_reports,
            "totalIncidents": total_incidents,
            "fusionRate": round((merged / total_reports * 100), 2) if total_reports else 0,
            "avgResponseMinutes": round(result.avgResponseMinutes or 0, 2),
            "resolvedRate": round((result.resolvedCount / total_reports * 100), 2) if total_reports else 0
        }

    @staticmethod
    def get_incident_type_distribution(db: Session, date_from, date_to):
        rows = db.query(
            Report.label.label("incidentType"),
            func.count().label("count")
        ).filter(
            Report.created_at.between(date_from, date_to)
        ).group_by(Report.label).all()

        return [{"incidentType": r.incidentType, "count": r.count} for r in rows]

    @staticmethod
    def get_hotspots(db: Session, date_from, date_to, limit):
        rows = db.query(
            Report.place_name.label("locationName"),
            func.count().label("incidentCount"),
            Report.lat,
            Report.lon
        ).filter(
            Report.created_at.between(date_from, date_to)
        ).group_by(Report.place_name, Report.lat, Report.lon)\
         .order_by(func.count().desc())\
         .limit(limit).all()

        return [
            {
                "locationName": r.locationName,
                "incidentCount": r.incidentCount,
                "lat": r.lat,
                "lng": r.lon
            }
            for r in rows
        ]

    @staticmethod
    def get_peak_time(db: Session, date_from, date_to):
        rows = db.query(
            func.extract("hour", Report.created_at).label("hour"),
            func.count().label("count")
        ).filter(
            Report.created_at.between(date_from, date_to)
        ).group_by("hour").order_by("hour").all()

        return [{"hour": int(r.hour), "count": r.count} for r in rows]

    @staticmethod
    def get_fusion_stats(db: Session, date_from, date_to):
        result = db.query(
            func.count().label("totalReports"),
            func.count(distinct(Report.incident_id)).label("totalIncidents")
        ).filter(
            Report.created_at.between(date_from, date_to)
        ).first()

        total_reports = result.totalReports or 0
        total_incidents = result.totalIncidents or 0
        merged = total_reports - total_incidents

        return {
            "totalReports": total_reports,
            "totalIncidents": total_incidents,
            "mergedReports": merged,
            "fusionRate": round((merged / total_reports * 100), 2) if total_reports else 0,
            "avgReportsPerIncident": round(total_reports / total_incidents, 2) if total_incidents else 0
        }

    @staticmethod
    def get_status_overview(db: Session, date_from, date_to):
        rows = db.query(
            Report.status,
            func.count().label("count")
        ).filter(
            Report.created_at.between(date_from, date_to)
        ).group_by(Report.status).all()

        return [{"status": r.status, "count": r.count} for r in rows]
