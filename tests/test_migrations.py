"""Tests for Alembic database migrations."""

import pytest
import sqlite3
import tempfile
import os


def create_old_schema_db(db_path: str) -> None:
    """Create a database with the old schema (without category_id)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create time_entries table without category_id column
    cursor.execute(
        """
        CREATE TABLE time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration_hours FLOAT DEFAULT 0.0,
            description TEXT,
            accumulated_pause_seconds FLOAT DEFAULT 0.0,
            last_pause_start_time TIMESTAMP,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Insert a test entry
    cursor.execute(
        """
        INSERT INTO time_entries (date, start_time, end_time, duration_hours, description)
        VALUES ('2026-01-27', '09:00', '17:00', 8.0, 'Test entry')
    """
    )

    conn.commit()
    conn.close()


def test_migration_adds_category_id_column():
    """Test that Alembic migration adds category_id column to existing database."""
    # Create a temporary database with old schema
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    try:
        create_old_schema_db(db_path)

        # Verify column doesn't exist before migration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.OperationalError) as exc_info:
            cursor.execute("SELECT category_id FROM time_entries LIMIT 1")
        assert "no such column" in str(exc_info.value)
        conn.close()

        # Run Alembic migrations using the database module
        from waqt.database import run_migrations

        run_migrations(db_path)

        # Verify column exists after migration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # This should not raise an error now
        cursor.execute("SELECT category_id FROM time_entries LIMIT 1")
        result = cursor.fetchone()
        assert result is not None  # The test entry exists
        assert result[0] is None  # category_id should be NULL

        # Verify categories table was created
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        )
        assert cursor.fetchone() is not None

        # Verify alembic_version table was created (migration tracking)
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    finally:
        os.close(db_fd)
        os.unlink(db_path)


def test_migration_is_idempotent():
    """Test that running Alembic migrations twice doesn't cause errors."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    try:
        create_old_schema_db(db_path)

        from waqt.database import run_migrations

        # Run migrations twice - should not raise any errors
        run_migrations(db_path)
        run_migrations(db_path)  # Second run should be no-op

        # Verify database is still functional
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT category_id FROM time_entries")
        entries = cursor.fetchall()
        assert len(entries) == 1
        conn.close()

    finally:
        os.close(db_fd)
        os.unlink(db_path)
