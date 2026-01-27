"""Standalone database configuration and session management.

This module provides SQLAlchemy database access independent of Flask,
enabling CLI and MCP Server to operate without Flask overhead while
sharing the same database with the web interface.
"""

from contextlib import contextmanager
from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.engine import Engine
import os
import sys
import shutil
import platformdirs

# Base class for all models
Base = declarative_base()

# Module-level engine and session factory
_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def get_database_path() -> str:
    """
    Resolve database path using the same logic as Flask app.

    Priority:
    1. WAQT_DATA_DIR environment variable
    2. Platform-specific user data directory (platformdirs)

    Returns:
        Absolute path to the SQLite database file.
    """
    custom_data_dir = os.environ.get("WAQT_DATA_DIR")
    if custom_data_dir:
        data_dir = os.path.abspath(custom_data_dir)
    else:
        data_dir = platformdirs.user_data_dir("waqt", "GMouaad")

    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "time_tracker.db")


def _get_legacy_db_candidates() -> list[str]:
    """Get list of legacy database paths to check for migration."""
    db_filename = "time_tracker.db"
    candidates = [
        # 1. Instance folder (common Flask location)
        os.path.abspath(os.path.join("instance", db_filename)),
        # 2. Current working directory
        os.path.abspath(db_filename),
    ]

    # If running as PyInstaller executable
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, db_filename))
        candidates.append(os.path.join(exe_dir, "instance", db_filename))

    return candidates


def _migrate_legacy_database(db_path: str) -> None:
    """Migrate database from legacy locations if needed."""
    if os.path.exists(db_path):
        return  # Already exists, no migration needed

    for legacy_path in _get_legacy_db_candidates():
        if os.path.exists(legacy_path) and os.path.isfile(legacy_path):
            try:
                print(f"Migrating database from {legacy_path} to {db_path}...")
                shutil.copy2(legacy_path, db_path)
                print("Migration successful.")
                return
            except Exception as e:
                print(f"Error migrating database from {legacy_path}: {e}")


def init_engine(database_url: Optional[str] = None) -> Engine:
    """
    Initialize the SQLAlchemy engine.

    Args:
        database_url: SQLAlchemy database URL. If None, uses default SQLite path.

    Returns:
        The SQLAlchemy Engine instance.
    """
    global _engine, _SessionFactory

    if database_url is None:
        db_path = get_database_path()
        _migrate_legacy_database(db_path)
        database_url = f"sqlite:///{db_path}"

    _engine = create_engine(database_url, echo=False)
    _SessionFactory = sessionmaker(bind=_engine)

    return _engine


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.

    Returns:
        The SQLAlchemy Engine instance.
    """
    if _engine is None:
        init_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the session factory.

    Returns:
        The sessionmaker instance.
    """
    if _SessionFactory is None:
        init_engine()
    return _SessionFactory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with get_session() as session:
            result = some_service_function(session, ...)
            # Auto-commits on success, rolls back on exception

    Yields:
        A SQLAlchemy Session instance.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """Create all tables in the database."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def run_migrations(db_path: Optional[str] = None) -> None:
    """
    Run Alembic database migrations.

    Args:
        db_path: Path to the database file. If None, uses default.
    """
    if db_path is None:
        db_path = get_database_path()

    try:
        from alembic.config import Config
        from alembic import command

        # Find alembic.ini - check multiple locations
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

        # Check for alembic.ini in project root
        alembic_ini = os.path.join(project_root, "alembic.ini")

        # For frozen executables, check relative to executable
        if not os.path.exists(alembic_ini) and getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            alembic_ini = os.path.join(exe_dir, "alembic.ini")

        if not os.path.exists(alembic_ini):
            # Alembic not available (e.g., frozen build without alembic)
            # Fall back to create_tables which handles basic schema
            print("Note: Alembic config not found, using basic table creation")
            return

        # Configure Alembic
        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        # Set the script location relative to alembic.ini
        alembic_dir = os.path.join(os.path.dirname(alembic_ini), "alembic")
        alembic_cfg.set_main_option("script_location", alembic_dir)

        # Run migrations to head
        command.upgrade(alembic_cfg, "head")

    except ImportError:
        # Alembic not installed, skip migrations
        print("Note: Alembic not installed, skipping migrations")
    except Exception as e:
        print(f"Warning: Failed to run Alembic migrations: {e}")


def initialize_database() -> None:
    """
    Full database initialization for CLI/MCP contexts.

    Creates tables, runs migrations, and seeds default settings.
    """
    from .models import Settings

    # Ensure engine is initialized
    get_engine()

    # Create tables
    create_tables()

    # Run migrations
    run_migrations()

    # Seed default settings
    with get_session() as session:
        default_settings = [
            ("standard_hours_per_day", "8"),
            ("weekly_hours", "40"),
            ("pause_duration_minutes", "45"),
            ("auto_end", "false"),
        ]

        for key, value in default_settings:
            existing = session.query(Settings).filter_by(key=key).first()
            if not existing:
                setting = Settings(key=key, value=value)
                session.add(setting)
