"""
Shared fixtures for all test modules.

Strategy:
 - Override the get_db dependency so FastAPI endpoints share the SAME
   session/transaction as the test.
 - Each test runs inside a transaction that is ROLLED BACK after the test
   so tests never pollute each other.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.enums import AuthProvider, UserRole
from app.core.security import create_access_token, hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.unit import Unit
from app.models.user import User


# ------------------------------------------------------------------ db
@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Ensure all tables exist before the test session starts."""
    init_db()


@pytest.fixture()
def db():
    """
    Provide a transactional DB session.
    Uses a SAVEPOINT so that all changes are rolled back after each test,
    including changes made inside API endpoints via the overridden get_db.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Begin a nested (SAVEPOINT) transaction
    nested = connection.begin_nested()

    # When the session calls commit(), advance to the next SAVEPOINT
    # instead of actually committing.
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ------------------------------------------------------------------ client
@pytest.fixture()
def client(db: Session):
    """
    FastAPI TestClient that shares the test's DB session.
    This ensures data created in fixtures is visible to API endpoints.
    """
    from app.db.session import get_db  # noqa: WPS433

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ------------------------------------------------------------------ users
@pytest.fixture()
def reporter_user(db: Session):
    """Create a REPORTER user and return (user, access_token)."""
    user = User(
        role=UserRole.REPORTER.value,
        auth_provider=AuthProvider.LIFF.value,
        line_user_id=f"test-line-reporter-{uuid.uuid4().hex[:8]}",
        line_display_name="Test Reporter",
        full_name="Test Reporter",
        reporter_type="STUDENT",
        is_active=True,
    )
    db.add(user)
    db.flush()

    token = create_access_token(
        subject=str(user.id),
        extra_data={"role": user.role, "auth_provider": user.auth_provider},
    )
    return user, token


@pytest.fixture()
def staff_user(db: Session):
    """Create a STAFF user with a unit and return (user, access_token, unit)."""
    unit = Unit(
        code=f"TEST_{uuid.uuid4().hex[:6].upper()}",
        name="Security (Test)",
        is_active=True,
    )
    db.add(unit)
    db.flush()

    user = User(
        role=UserRole.STAFF.value,
        auth_provider=AuthProvider.LOCAL.value,
        email=f"staff-{uuid.uuid4().hex[:6]}@tu.ac.th",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Staff",
        unit_id=unit.id,
        is_active=True,
    )
    db.add(user)
    db.flush()

    token = create_access_token(
        subject=str(user.id),
        extra_data={"role": user.role, "auth_provider": user.auth_provider},
    )
    return user, token, unit


@pytest.fixture()
def auth_header(reporter_user):
    """Bearer header for reporter."""
    _, token = reporter_user
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def staff_auth_header(staff_user):
    """Bearer header for staff."""
    _, token, _ = staff_user
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db: Session):
    """Create an ADMIN user and return (user, access_token)."""
    user = User(
        role=UserRole.ADMIN.value,
        auth_provider=AuthProvider.LOCAL.value,
        email=f"admin-{uuid.uuid4().hex[:6]}@tu.ac.th",
        password_hash=hash_password("AdminPass1!"),
        full_name="Test Admin",
        is_active=True,
    )
    db.add(user)
    db.flush()

    token = create_access_token(
        subject=str(user.id),
        extra_data={"role": user.role, "auth_provider": user.auth_provider},
    )
    return user, token


@pytest.fixture()
def admin_auth_header(admin_user):
    """Bearer header for admin."""
    _, token = admin_user
    return {"Authorization": f"Bearer {token}"}
