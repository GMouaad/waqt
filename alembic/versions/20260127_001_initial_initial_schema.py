"""Initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2026-01-27

This migration creates all tables and handles existing databases by:
1. Using CREATE TABLE IF NOT EXISTS for new installs
2. Using batch operations for SQLite ALTER TABLE compatibility
3. Gracefully handling already-existing columns
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Create all tables, handling existing databases gracefully."""

    # Create categories table if not exists
    if not table_exists("categories"):
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("code", sa.String(20), unique=True, nullable=True),
            sa.Column("color", sa.String(20), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("created_at", sa.DateTime()),
        )

    # Create time_entries table if not exists
    if not table_exists("time_entries"):
        op.create_table(
            "time_entries",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("date", sa.Date(), nullable=False, index=True),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("duration_hours", sa.Float(), nullable=False),
            sa.Column("accumulated_pause_seconds", sa.Float(), default=0.0),
            sa.Column("last_pause_start_time", sa.DateTime(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column(
                "category_id",
                sa.Integer(),
                sa.ForeignKey("categories.id"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime()),
        )
    else:
        # Table exists - add missing columns for existing databases
        # Use batch mode for SQLite compatibility
        with op.batch_alter_table("time_entries") as batch_op:
            if not column_exists("time_entries", "accumulated_pause_seconds"):
                batch_op.add_column(
                    sa.Column("accumulated_pause_seconds", sa.Float(), default=0.0)
                )

            if not column_exists("time_entries", "last_pause_start_time"):
                batch_op.add_column(
                    sa.Column("last_pause_start_time", sa.DateTime(), nullable=True)
                )

            if not column_exists("time_entries", "is_active"):
                batch_op.add_column(sa.Column("is_active", sa.Boolean(), default=False))

            if not column_exists("time_entries", "category_id"):
                batch_op.add_column(
                    sa.Column("category_id", sa.Integer(), nullable=True)
                )
                # Note: SQLite doesn't support adding FK constraints to existing tables easily
                # The relationship will still work, just without DB-level enforcement

    # Create leave_days table if not exists
    if not table_exists("leave_days"):
        op.create_table(
            "leave_days",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("date", sa.Date(), nullable=False, index=True),
            sa.Column("leave_type", sa.String(20), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )

    # Create settings table if not exists
    if not table_exists("settings"):
        op.create_table(
            "settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("key", sa.String(50), nullable=False, unique=True),
            sa.Column("value", sa.String(200), nullable=False),
        )


def downgrade() -> None:
    """Drop all tables (use with caution!)."""
    op.drop_table("settings")
    op.drop_table("leave_days")
    op.drop_table("time_entries")
    op.drop_table("categories")
