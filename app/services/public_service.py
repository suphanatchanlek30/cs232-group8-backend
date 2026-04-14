import math

from sqlalchemy.orm import Session

from app.core.enums import IncidentLabel, ReporterType
from app.models.location import Location
from app.schemas.public import (
    LocationItem,
    LocationListResponseData,
    PaginationMeta,
    ReportOptionsResponseData,
    SystemInfoResponseData,
)


class PublicService:
    @staticmethod
    def get_system_info() -> dict:
        data = SystemInfoResponseData(
            systemName="TU Pulse",
            projectNameEn="Campus Incident Intelligence Platform",
            allowReportSubmission=True,
            version="v1",
        )
        return data.model_dump()

    @staticmethod
    def get_report_options() -> dict:
        data = ReportOptionsResponseData(
            incidentLabels=[e.value for e in IncidentLabel],
            reporterTypes=[e.value for e in ReporterType],
        )
        return data.model_dump()

    @staticmethod
    def get_locations(
        db: Session,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = db.query(Location).filter(Location.is_active.is_(True))

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Location.location_name.ilike(pattern)
                | Location.building_code.ilike(pattern)
            )

        total_items = query.count()
        total_pages = max(1, math.ceil(total_items / page_size))

        items = (
            query.order_by(Location.location_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        data = LocationListResponseData(
            items=[
                LocationItem(
                    locationId=str(loc.id),
                    locationName=loc.location_name,
                    buildingCode=loc.building_code,
                    campusZone=loc.campus_zone,
                    lat=float(loc.lat) if loc.lat is not None else None,
                    lng=float(loc.lng) if loc.lng is not None else None,
                )
                for loc in items
            ],
            pagination=PaginationMeta(
                page=page,
                pageSize=page_size,
                totalItems=total_items,
                totalPages=total_pages,
            ),
        )
        return data.model_dump()
