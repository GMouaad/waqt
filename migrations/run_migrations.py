import sqlite3
import os
import sys


def get_db_path():
    """Locate the database file."""
    # Prioritize instance folder as that seems to be where it ends up
    possible_paths = [
        "instance/time_tracker.db",
        "time_tracker.db",
        "src/instance/time_tracker.db",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def run_migrations(db_path=None):
    """Run all database migrations."""
    if not db_path:
        db_path = get_db_path()

    if not db_path:
        return

    # Handle file:// URI if passed from SQLAlchemy config
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")
        # Handle relative paths in SQLAlchemy URIs
        if not os.path.isabs(db_path):
            # Flask-SQLAlchemy 3+ puts relative dbs in instance folder
            instance_path = os.path.join(os.getcwd(), "instance", db_path)
            root_path = os.path.join(os.getcwd(), db_path)

            if os.path.exists(instance_path):
                db_path = instance_path
            elif os.path.exists(root_path):
                db_path = root_path
            else:
                # If neither exists, db.create_all() likely hasn't created it yet
                # or it's about to be created in instance/ (default)
                db_path = instance_path

    if not os.path.exists(db_path):
        return

    print(f"🔧 Running migrations on: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the main table exists before proceeding
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='time_entries'"
        )
        if not cursor.fetchone():
            print(
                "  Table 'time_entries' not found. Skipping migrations (likely a new database)."
            )
            conn.close()
            return

        # Define migrations
        migrations = [
            {
                "name": "Add pause feature columns",
                "sql": [
                    "ALTER TABLE time_entries ADD COLUMN accumulated_pause_seconds FLOAT DEFAULT 0.0",
                    "ALTER TABLE time_entries ADD COLUMN last_pause_start_time TIMESTAMP",
                ],
                "check": "SELECT accumulated_pause_seconds FROM time_entries LIMIT 1",
            },
            {
                "name": "Add is_active column",
                "sql": [
                    "ALTER TABLE time_entries ADD COLUMN is_active BOOLEAN DEFAULT 0"
                ],
                "check": "SELECT is_active FROM time_entries LIMIT 1",
                "post_sql": """
                    UPDATE time_entries 
                    SET is_active = 1 
                    WHERE duration_hours = 0.0 AND start_time = end_time
                """,
            },
            {
                "name": "Add categories table and relation",
                "sql": [
                    """CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        code VARCHAR(20) UNIQUE,
                        color VARCHAR(20),
                        description TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )""",
                    "ALTER TABLE time_entries ADD COLUMN category_id INTEGER REFERENCES categories(id)",
                ],
                "check": """
                    SELECT time_entries.category_id
                    FROM time_entries
                    JOIN categories ON time_entries.category_id = categories.id
                    LIMIT 1
                """,
            },
        ]

        for migration in migrations:
            try:
                # Check if already applied
                try:
                    cursor.execute(migration["check"])
                    continue
                except sqlite3.OperationalError:
                    # Column likely missing, proceed with migration
                    pass

                print(f"  Applying migration: {migration['name']}...")
                # Apply SQL commands
                for sql in migration["sql"]:
                    try:
                        cursor.execute(sql)
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            pass
                        elif "no such table" in str(e):
                            print(
                                f"    ❌ Error: Table not found. Is the database initialized?"
                            )
                            break
                        else:
                            raise e

                # Run post-migration SQL if any
                if "post_sql" in migration:
                    cursor.execute(migration["post_sql"])

                print(f"    ✅ Applied successfully.")

            except Exception as e:
                print(f"    ❌ Migration '{migration['name']}' failed: {e}")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


if __name__ == "__main__":
    run_migrations()
