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