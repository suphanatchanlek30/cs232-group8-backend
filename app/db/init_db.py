from app.db.base import Base
from app.db.session import engine

# important: import all models before create_all
from app.models import (  # noqa: F401
    audit_log,
    incident,
    incident_comment,
    incident_report,
    incident_status_history,
    location,
    notification,
    refresh_token,
    report,
    report_attachment,
    report_detected_label,
    routing_rule,
    unit,
    user,
)


def init_db():
    Base.metadata.create_all(bind=engine)