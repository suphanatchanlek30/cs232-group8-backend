from sqlalchemy import text
from app.db.session import SessionLocal, engine

def migrate():
    with engine.connect() as conn:
        print("Adding location_note to reports table...")
        try:
            conn.execute(text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS location_note VARCHAR(255)"))
            conn.commit()
            print("Successfully added location_note to reports.")
        except Exception as e:
            print(f"Error adding to reports: {e}")

        print("Adding location_note to incidents table...")
        try:
            conn.execute(text("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS location_note VARCHAR(255)"))
            conn.commit()
            print("Successfully added location_note to incidents.")
        except Exception as e:
            print(f"Error adding to incidents: {e}")

if __name__ == "__main__":
    migrate()
