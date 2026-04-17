from pydantic import BaseModel
from typing import List, Optional


class KpiSummary(BaseModel):
    totalReports: int
    totalIncidents: int
    fusionRate: float
    avgResponseMinutes: float
    resolvedRate: float


class IncidentTypeItem(BaseModel):
    incidentType: str
    count: int


class HotspotItem(BaseModel):
    locationName: str
    incidentCount: int
    lat: float
    lng: float


class PeakTimeItem(BaseModel):
    hour: int
    count: int


class FusionStats(BaseModel):
    totalReports: int
    totalIncidents: int
    mergedReports: int
    fusionRate: float
    avgReportsPerIncident: float


class StatusItem(BaseModel):
    status: str
    count: int
