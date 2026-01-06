"""Unit tests for the time tracker application."""
import pytest
from datetime import time, date
from src.waqtracker import create_app, db
from src.waqtracker.models import TimeEntry, LeaveDay, Settings
from src.waqtracker.utils import calculate_duration, calculate_daily_overtime, get_week_bounds


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


def test_app_creation(app):
    """Test that the app is created successfully."""
    assert app is not None
    assert app.config['TESTING'] is True


def test_calculate_duration():
    """Test duration calculation between two times."""
    start = time(9, 0)
    end = time(17, 0)
    duration = calculate_duration(start, end)
    assert duration == 8.0
    
    # Test with minutes
    start = time(9, 30)
    end = time(17, 45)
    duration = calculate_duration(start, end)
    assert duration == 8.25


def test_calculate_daily_overtime():
    """Test overtime calculation."""
    # No overtime
    overtime = calculate_daily_overtime(8.0)
    assert overtime == 0.0
    
    # With overtime
    overtime = calculate_daily_overtime(10.0)
    assert overtime == 2.0
    
    # Under standard hours
    overtime = calculate_daily_overtime(6.0)
    assert overtime == 0.0


def test_get_week_bounds():
    """Test getting week boundaries."""
    # Monday
    test_date = date(2024, 1, 1)  # This is a Monday
    start, end = get_week_bounds(test_date)
    assert start.weekday() == 0  # Monday
    assert end.weekday() == 6  # Sunday
    assert (end - start).days == 6


def test_index_route(client):
    """Test the index/dashboard route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_time_entry_form(client):
    """Test the time entry form page."""
    response = client.get('/time-entry')
    assert response.status_code == 200
    assert b'Add Time Entry' in response.data


def test_reports_page(client):
    """Test the reports page."""
    response = client.get('/reports')
    assert response.status_code == 200
    assert b'Reports' in response.data


def test_leave_page(client):
    """Test the leave management page."""
    response = client.get('/leave')
    assert response.status_code == 200
    assert b'Leave Management' in response.data


def test_create_time_entry(app):
    """Test creating a time entry in the database."""
    with app.app_context():
        entry = TimeEntry(
            date=date(2024, 1, 1),
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_hours=8.0,
            description="Test work"
        )
        db.session.add(entry)
        db.session.commit()
        
        # Verify it was saved
        saved_entry = TimeEntry.query.first()
        assert saved_entry is not None
        assert saved_entry.description == "Test work"
        assert saved_entry.duration_hours == 8.0


def test_create_leave_day(app):
    """Test creating a leave day in the database."""
    with app.app_context():
        leave = LeaveDay(
            date=date(2024, 1, 15),
            leave_type='vacation',
            description='Family vacation'
        )
        db.session.add(leave)
        db.session.commit()
        
        # Verify it was saved
        saved_leave = LeaveDay.query.first()
        assert saved_leave is not None
        assert saved_leave.leave_type == 'vacation'
        assert saved_leave.description == 'Family vacation'


def test_settings_model(app):
    """Test the settings model."""
    with app.app_context():
        # Set a setting
        Settings.set_setting('test_key', 'test_value')
        
        # Get the setting
        value = Settings.get_setting('test_key')
        assert value == 'test_value'
        
        # Get non-existent setting with default
        value = Settings.get_setting('nonexistent', 'default')
        assert value == 'default'
