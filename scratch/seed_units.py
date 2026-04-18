import uuid
from sqlalchemy import create_engine
from app.db.session import SessionLocal
from app.models.unit import Unit

def seed_units():
    db = SessionLocal()
    try:
        units_to_seed = [
            {"code": "SEC", "name": "ฝ่ายรักษาความปลอดภัย"},
            {"code": "FAC", "name": "ฝ่ายอาคารสถานที่"},
            {"code": "ENV", "name": "ฝ่ายสิ่งแวดล้อม"},
            {"code": "ITS", "name": "ฝ่ายไอที"}
        ]
        
        for u_data in units_to_seed:
            existing = db.query(Unit).filter(Unit.code == u_data["code"]).first()
            if not existing:
                print(f"Seeding unit: {u_data['name']}")
                unit = Unit(
                    code=u_data["code"],
                    name=u_data["name"],
                    is_active=True
                )
                db.add(unit)
            else:
                print(f"Unit {u_data['code']} already exists.")
        
        db.commit()
    except Exception as e:
        print(f"Error seeding units: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_units()
