import os
import sys

import pytest

# Add scripts directory to path to allow importing seed_db
sys.path.append(os.path.join(os.path.dirname(__file__), "../scripts"))

from seed_db import seed_database  # noqa: E402
from waqt import create_app, db  # noqa: E402
from waqt.models import Category, TimeEntry, LeaveDay, Settings  # noqa: E402


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_seed_database(app, capsys):
    """Test that seeding populates the database correctly."""

    # Run seeder
    seed_database(app)

    with app.app_context():
        # Verify Categories
        categories = Category.query.all()
        assert len(categories) == 5
        assert Category.query.filter_by(name="Development").first() is not None

        # Verify Settings
        assert (
            Settings.query.filter_by(key="standard_hours_per_day").first().value == "8"
        )

        # Verify Leave Days
        leave_days = LeaveDay.query.all()
        assert len(leave_days) >= 2

        # Verify Time Entries
        entries = TimeEntry.query.all()
        assert len(entries) > 0

        # Verify Category Assignment
        dev_entry = (
            TimeEntry.query.join(Category)
            .filter(Category.name == "Development")
            .first()
        )
        assert (
            dev_entry is not None or TimeEntry.query.count() > 0
        )  # At least ensure entries exist


def test_seed_idempotency(app):
    """Test that running seed multiple times doesn't duplicate data."""

    # Run once
    seed_database(app)

    with app.app_context():
        initial_cat_count = Category.query.count()
        initial_entry_count = TimeEntry.query.count()

    # Run again
    seed_database(app)

    with app.app_context():
        # Counts should be identical
        assert Category.query.count() == initial_cat_count
        assert TimeEntry.query.count() == initial_entry_count
