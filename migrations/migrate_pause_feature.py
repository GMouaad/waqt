import sqlite3
import os

def migrate():
    # Check possible database locations
    possible_paths = ["instance/time_tracker.db", "time_tracker.db"]
    db_path = None
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
            
    if not db_path:
        print("Database file not found. Skipping migration (will be created by init_db.py if needed).")
        return

    print(f"Migrating database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE time_entries ADD COLUMN accumulated_pause_seconds FLOAT DEFAULT 0.0")
        print("Added accumulated_pause_seconds column.")
    except sqlite3.OperationalError:
        print("Column accumulated_pause_seconds already exists.")

    try:
        cursor.execute("ALTER TABLE time_entries ADD COLUMN last_pause_start_time TIMESTAMP")
        print("Added last_pause_start_time column.")
    except sqlite3.OperationalError:
        print("Column last_pause_start_time already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
