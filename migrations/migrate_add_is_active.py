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
        print(
            "Database file not found. Skipping migration (will be created by init_db.py if needed)."
        )
        return

    print(f"Migrating database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "ALTER TABLE time_entries ADD COLUMN is_active BOOLEAN DEFAULT 0"
        )
        print("Added is_active column.")

        # Backfill existing active entries
        # We use the old heuristic to find entries that SHOULD be active and set the flag
        # But wait, the whole point is that heuristic is flawed.
        # However, for migration, it's the best we have to preserve state of currently running timers.
        # It's better to migrate them as active than lose the active status.
        # Users can stop them if they are actually manual entries.

        print("Backfilling is_active status for potentially running timers...")
        cursor.execute(
            """
            UPDATE time_entries
            SET is_active = 1
            WHERE duration_hours = 0.0 AND start_time = end_time
        """
        )
        print(f"Updated {cursor.rowcount} entries to be active.")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column is_active already exists.")
        else:
            print(f"Error adding column: {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
