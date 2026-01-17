from .run_migrations import run_migrations
import sqlite3
import os
import platformdirs

def migrate():
    # Logic matching src/waqt/__init__.py
    custom_data_dir = os.environ.get("WAQT_DATA_DIR")
    if custom_data_dir:
        data_dir = os.path.abspath(custom_data_dir)
    else:
        data_dir = platformdirs.user_data_dir("waqt", "GMouaad")
    
    db_path = os.path.join(data_dir, "time_tracker.db")
    
    # Fallback to local instance if platform dir db doesn't exist but local does (dev mode)
    if not os.path.exists(db_path):
        possible_paths = ["instance/time_tracker.db", "time_tracker.db", "src/instance/time_tracker.db"]
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break

    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path} or local fallbacks. Skipping migration.")
        return

    print(f"Migrating database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create Categories Table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                code VARCHAR(20) UNIQUE,
                color VARCHAR(20),
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created/Verified categories table.")
    except Exception as e:
        print(f"Error creating categories table: {e}")

    # 2. Add category_id to time_entries
    try:
        cursor.execute("ALTER TABLE time_entries ADD COLUMN category_id INTEGER REFERENCES categories(id)")
        print("Added category_id column to time_entries.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column category_id already exists in time_entries.")
        else:
            print(f"Error adding column: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
