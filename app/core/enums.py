from enum import Enum


class UserRole(str, Enum):
    REPORTER = "REPORTER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"


class AuthProvider(str, Enum):
    LIFF = "LIFF"
    LOCAL = "LOCAL"
    SYSTEM = "SYSTEM"


class ReporterType(str, Enum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    VISITOR = "VISITOR"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class IncidentLabel(str, Enum):
    FIRE_SMOKE = "fire_smoke"
    WATER_LEAK = "water_leak"
    WASTE_ISSUE = "waste_issue"
    FACILITY_ISSUE = "facility_issue"
    SECURITY_ISSUE = "security_issue"


class ReportStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    LINKED = "LINKED"
    REJECTED = "REJECTED"


class IncidentStatus(str, Enum):
    NEW = "NEW"
    IN_REVIEW = "IN_REVIEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"