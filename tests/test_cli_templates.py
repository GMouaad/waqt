import pytest
from click.testing import CliRunner
from datetime import date, time
from src.waqt.models import Template, TimeEntry


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    from src.waqt import create_app, db

    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def cli():
    """Return the CLI entry point."""
    from src.waqt.cli import cli as cli_obj

    return cli_obj


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


def test_template_create_basic(runner, app, cli):
    """Test creating a template."""
    with app.app_context():
        result = runner.invoke(
            cli,
            [
                "template",
                "create",
                "Morning Routine",
                "--start",
                "09:00",
                "--duration",
                "60",
            ],
        )
        assert result.exit_code == 0
        assert "Template 'Morning Routine' created" in result.output

        t = Template.query.filter_by(name="Morning Routine").first()
        assert t is not None
        assert t.start_time == time(9, 0)
        assert t.duration_minutes == 60


def test_template_list(runner, app, cli):
    """Test listing templates."""
    from src.waqt import db

    with app.app_context():
        t1 = Template(
            name="T1", start_time=time(9, 0), duration_minutes=60, description="Test 1"
        )
        t2 = Template(
            name="T2", start_time=time(10, 0), duration_minutes=30, description="Test 2"
        )
        db.session.add(t1)
        db.session.add(t2)
        db.session.commit()

        result = runner.invoke(cli, ["template", "list"])
        assert result.exit_code == 0
        assert "T1" in result.output
        assert "T2" in result.output
        assert "60m" in result.output


def test_template_show(runner, app, cli):
    """Test showing template details."""
    from src.waqt import db

    with app.app_context():
        t = Template(
            name="ShowMe",
            start_time=time(9, 0),
            duration_minutes=60,
            description="Details",
        )
        db.session.add(t)
        db.session.commit()

        result = runner.invoke(cli, ["template", "show", "ShowMe"])
        assert result.exit_code == 0
        assert "ShowMe" in result.output
        assert "Details" in result.output
        assert "09:00" in result.output


def test_template_delete(runner, app, cli):
    """Test deleting a template."""
    from src.waqt import db

    with app.app_context():
        t = Template(name="DeleteMe", start_time=time(9, 0), duration_minutes=60)
        db.session.add(t)
        db.session.commit()

        result = runner.invoke(cli, ["template", "delete", "DeleteMe"], input="y")
        assert result.exit_code == 0
        assert "deleted successfully" in result.output

        assert Template.query.filter_by(name="DeleteMe").first() is None


def test_template_apply_command(runner, app, cli):
    """Test applying a template via CLI."""
    from src.waqt import db

    with app.app_context():
        t = Template(
            name="Work",
            start_time=time(9, 0),
            duration_minutes=480,
            description="Full day",
        )
        db.session.add(t)
        db.session.commit()

        target_date = date(2025, 5, 20)
        result = runner.invoke(
            cli, ["apply", "Work", "--date", target_date.isoformat()]
        )
        assert result.exit_code == 0
        assert "Applied template 'Work'" in result.output

        entry = TimeEntry.query.filter_by(date=target_date).first()
        assert entry is not None
        assert entry.description == "Full day"
        # Default pause is 45m. 8h - 45m = 7.25h
        assert entry.duration_hours == 7.25


def test_add_command_with_template(runner, app, cli):
    """Test 'add --template' functionality."""
    from src.waqt import db

    with app.app_context():
        t = Template(name="ShortEntry", start_time=time(14, 0), duration_minutes=30)
        db.session.add(t)
        db.session.commit()

        target_date = date(2025, 5, 21)
        # Using add with --template should pre-fill values but allow overrides if specified
        # But 'add --template' logic in CLI usually just delegates to apply_template or similar?
        # Let's check logic. Based on plan, 'add' has --template option.

        result = runner.invoke(
            cli, ["add", "--template", "ShortEntry", "--date", target_date.isoformat()]
        )
        assert result.exit_code == 0
        assert "Time entry added successfully" in result.output
        assert "via template 'ShortEntry'" in result.output

        entry = TimeEntry.query.filter_by(date=target_date).first()
        assert entry is not None
        assert entry.start_time == time(14, 0)
