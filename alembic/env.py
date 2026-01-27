"""Alembic environment configuration for Waqt time tracker.

This module configures how Alembic runs migrations, including:
- Database connection setup using waqt.database
- Model metadata for autogenerate support
- Online and offline migration modes
"""

from logging.config import fileConfig

from sqlalchemy import pool, text
from sqlalchemy import create_engine

from alembic import context

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models to ensure they're registered with Base.metadata
# This must happen before we access target_metadata
import sys
import os

# Add src to path so we can import waqt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from waqt.database import Base, get_database_path
from waqt import models  # noqa: F401 - Import to register models

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    """Get the database URL, using waqt's database path logic."""
    # Check if URL is provided via config (e.g., for testing)
    url = config.get_main_option("sqlalchemy.url")
    if url and not url.endswith("instance/time_tracker.db"):
        return url

    # Use waqt's database path resolution
    db_path = get_database_path()
    return f"sqlite:///{db_path}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    allowing SQL to be generated without a database connection.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    url = get_url()

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
