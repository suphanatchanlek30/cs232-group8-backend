"""
Seed script: สร้าง staff/admin user สำหรับทดสอบ

Usage:
    docker compose exec api python -m app.db.seed_staff

หรือ run ตรง:
    python -m app.db.seed_staff
"""

from app.core.enums import AuthProvider, UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.unit import Unit
from app.models.user import User


SEED_UNITS = [
    {"code": "SECURITY", "name": "Security", "description": "หน่วยรักษาความปลอดภัย"},
    {"code": "MAINTENANCE", "name": "Maintenance", "description": "หน่วยซ่อมบำรุง"},
]

SEED_STAFF = [
    {
        "email": "security@tu.ac.th",
        "password": "Password123!",
        "full_name": "Somying Jaidee",
        "role": UserRole.STAFF.value,
        "unit_code": "SECURITY",
    },
    {
        "email": "admin@tu.ac.th",
        "password": "Password123!",
        "full_name": "Admin TU Pulse",
        "role": UserRole.ADMIN.value,
        "unit_code": None,
    },
]


def seed():
    db = SessionLocal()
    try:
        # ----- seed units -----
        for u in SEED_UNITS:
            existing = db.query(Unit).filter(Unit.code == u["code"]).first()
            if not existing:
                db.add(Unit(**u, is_active=True))
                print(f"  + Unit created: {u['code']}")
            else:
                print(f"  · Unit exists : {u['code']}")
        db.flush()

        # ----- seed staff users -----
        for s in SEED_STAFF:
            existing = db.query(User).filter(User.email == s["email"]).first()
            if existing:
                print(f"  · User exists : {s['email']}")
                continue

            unit_id = None
            if s["unit_code"]:
                unit = db.query(Unit).filter(Unit.code == s["unit_code"]).first()
                if unit:
                    unit_id = unit.id

            user = User(
                role=s["role"],
                auth_provider=AuthProvider.LOCAL.value,
                email=s["email"],
                password_hash=hash_password(s["password"]),
                full_name=s["full_name"],
                unit_id=unit_id,
                is_active=True,
            )
            db.add(user)
            print(f"  + User created : {s['email']} ({s['role']})")

        db.commit()
        print("\n✅  Seed completed!")
    except Exception as exc:
        db.rollback()
        print(f"\n❌  Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # ensure tables exist before seeding
    from app.db.init_db import init_db
    init_db()
    seed()
