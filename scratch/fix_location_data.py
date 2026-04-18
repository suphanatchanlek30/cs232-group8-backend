from sqlalchemy import text
from app.db.session import engine

BUILDING_MAP = {
    "LC5": "อาคาร บร.5 (LC5)",
    "LC2": "อาคาร บร.2 (LC2)",
    "LC3": "อาคาร บร.3 (LC3)",
    "SC3": "อาคารเรียนรวม สังคมศาสตร์ 3 (SC3)",
    "SC1": "อาคารเรียนรวมกลุ่มสังคมศาสตร์ 1 (SC1)",
    "OTHER": "Other / อื่นๆ"
}

def fix_data():
    with engine.connect() as conn:
        print("Cleaning up location names in reports and incidents...")
        
        for code, label in BUILDING_MAP.items():
            # Update incidents
            conn.execute(text(f"UPDATE incidents SET location_name_snapshot = :label WHERE location_name_snapshot = :code"), {"label": label, "code": code})
            # Update reports
            conn.execute(text(f"UPDATE reports SET location_name_snapshot = :label WHERE location_name_snapshot = :code"), {"label": label, "code": code})
        
        # Also fix the "notes" that were stored as names if we can recognize them
        # For example, if it says "หน้าตึก LC" it's probably LC5 or similar. 
        # But we don't want to guess wrongly. 
        # For now, let's just fix the ones that are exact codes.
        
        conn.commit()
        print("Done cleaning up data.")

if __name__ == "__main__":
    fix_data()
