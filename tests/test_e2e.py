"""End-to-end browser tests using Playwright."""

import pytest
from datetime import datetime


@pytest.mark.e2e
def test_homepage_loads(page, live_server):
    """Test that the homepage loads successfully."""
    page.goto(live_server)
    
    # Check that the page title contains "Waqt"
    assert "Waqt" in page.title()
    
    # Check for key navigation elements
    assert page.get_by_test_id("navbar").is_visible()
    assert page.get_by_test_id("logo").is_visible()
    assert page.get_by_test_id("nav-dashboard").is_visible()
    assert page.get_by_test_id("nav-time-entry").is_visible()
    assert page.get_by_test_id("nav-reports").is_visible()
    assert page.get_by_test_id("nav-leave").is_visible()


@pytest.mark.e2e
def test_navigation(page, live_server):
    """Test navigation between pages."""
    page.goto(live_server)
    
    # Navigate to Time Entry page
    page.get_by_test_id("nav-time-entry").click()
    page.wait_for_url(f"{live_server}/time-entry")
    assert page.get_by_test_id("time-entry-page").is_visible()
    
    # Navigate to Reports page
    page.get_by_test_id("nav-reports").click()
    page.wait_for_url(f"{live_server}/reports*")
    assert page.get_by_test_id("reports-page").is_visible()
    
    # Navigate to Leave page
    page.get_by_test_id("nav-leave").click()
    page.wait_for_url(f"{live_server}/leave")
    assert page.get_by_test_id("leave-page").is_visible()
    
    # Navigate back to Dashboard
    page.get_by_test_id("nav-dashboard").click()
    page.wait_for_url(live_server + "/")
    assert page.get_by_test_id("dashboard").is_visible()


@pytest.mark.e2e
def test_add_time_entry(page, live_server):
    """Test adding a time entry through the UI."""
    page.goto(f"{live_server}/time-entry")
    
    # Fill out the time entry form
    today = datetime.now().date().isoformat()
    page.get_by_test_id("input-date").fill(today)
    page.get_by_test_id("input-start-time").fill("09:00")
    page.get_by_test_id("input-end-time").fill("17:00")
    page.get_by_test_id("input-description").fill("Working on E2E tests")
    
    # Submit the form
    page.get_by_test_id("btn-submit").click()
    
    # Should redirect to dashboard
    page.wait_for_url(live_server + "/")
    
    # Check for success message
    flash_success = page.get_by_test_id("flash-success")
    assert flash_success.is_visible()
    assert "successfully" in flash_success.text_content().lower()
    
    # Check that the entry appears in the recent entries table
    recent_table = page.get_by_test_id("recent-entries-table")
    assert recent_table.is_visible()
    assert "Working on E2E tests" in recent_table.text_content()


@pytest.mark.e2e
def test_add_time_entry_validation(page, live_server):
    """Test time entry form validation."""
    page.goto(f"{live_server}/time-entry")
    
    # Try to submit empty form (browser validation should prevent submission)
    page.get_by_test_id("btn-submit").click()
    
    # Should still be on time entry page
    assert page.get_by_test_id("time-entry-page").is_visible()


@pytest.mark.e2e
def test_delete_time_entry(page, live_server):
    """Test deleting a time entry."""
    # First, add a time entry
    page.goto(f"{live_server}/time-entry")
    today = datetime.now().date().isoformat()
    page.get_by_test_id("input-date").fill(today)
    page.get_by_test_id("input-start-time").fill("10:00")
    page.get_by_test_id("input-end-time").fill("12:00")
    page.get_by_test_id("input-description").fill("Test entry to delete")
    page.get_by_test_id("btn-submit").click()
    
    # Wait for redirect to dashboard
    page.wait_for_url(live_server + "/")
    
    # Find the delete button and click it
    # Handle the confirmation dialog
    page.on("dialog", lambda dialog: dialog.accept())
    
    # Find the first delete button and click it
    delete_button = page.locator('[data-testid^="btn-delete-entry-"]').first
    delete_button.click()
    
    # Wait for the success message to appear
    flash_success = page.get_by_test_id("flash-success")
    flash_success.wait_for(state="visible")
    
    # Check for success message
    assert flash_success.is_visible()
    assert "deleted" in flash_success.text_content().lower()


@pytest.mark.e2e
def test_add_leave_day(page, live_server):
    """Test adding a leave day through the UI."""
    page.goto(f"{live_server}/leave")
    
    # Fill out the leave form
    today = datetime.now().date().isoformat()
    page.get_by_test_id("input-leave-date").fill(today)
    page.get_by_test_id("select-leave-type").select_option("vacation")
    page.get_by_test_id("input-leave-description").fill("Summer vacation")
    
    # Submit the form
    page.get_by_test_id("btn-add-leave").click()
    
    # Should stay on leave page
    page.wait_for_url(f"{live_server}/leave")
    
    # Check for success message
    flash_success = page.get_by_test_id("flash-success")
    assert flash_success.is_visible()
    assert "successfully" in flash_success.text_content().lower()
    
    # Check that the leave appears in the history table
    leave_table = page.get_by_test_id("leave-history-table")
    assert leave_table.is_visible()
    assert "Summer vacation" in leave_table.text_content()
    
    # Check that vacation count increased
    vacation_stat = page.get_by_test_id("stat-vacation-days")
    assert vacation_stat.is_visible()


@pytest.mark.e2e
def test_reports_week_view(page, live_server):
    """Test the weekly reports view."""
    page.goto(f"{live_server}/reports")
    
    # Verify we're on reports page
    assert page.get_by_test_id("reports-page").is_visible()
    
    # Check that week view is active by default
    week_button = page.get_by_test_id("btn-week-view")
    assert "btn-primary" in week_button.get_attribute("class")
    
    # Check for stats cards
    assert page.get_by_test_id("stat-total-hours").is_visible()
    assert page.get_by_test_id("stat-overtime").is_visible()
    assert page.get_by_test_id("stat-working-days").is_visible()
    
    # Check for date navigation
    assert page.get_by_test_id("date-navigator").is_visible()
    assert page.get_by_test_id("btn-prev-period").is_visible()
    assert page.get_by_test_id("btn-next-period").is_visible()
    assert page.get_by_test_id("current-period").is_visible()


@pytest.mark.e2e
def test_reports_month_view(page, live_server):
    """Test the monthly reports view."""
    page.goto(f"{live_server}/reports")
    
    # Switch to month view
    page.get_by_test_id("btn-month-view").click()
    page.wait_for_url(f"{live_server}/reports*period=month*")
    
    # Check that month view is active
    month_button = page.get_by_test_id("btn-month-view")
    assert "btn-primary" in month_button.get_attribute("class")
    
    # Check for leave days stat (only in month view)
    assert page.get_by_test_id("stat-leave-days").is_visible()


@pytest.mark.e2e
def test_reports_navigation(page, live_server):
    """Test navigating between different periods in reports."""
    page.goto(f"{live_server}/reports")
    
    # Get the current period text
    current_period = page.get_by_test_id("current-period").text_content()
    
    # Click next period
    page.get_by_test_id("btn-next-period").click()
    
    # Wait for the period text to change
    page.get_by_test_id("current-period").wait_for(state="attached")
    
    # Period should have changed
    new_period = page.get_by_test_id("current-period").text_content()
    assert new_period != current_period
    
    # Click previous period twice to go back
    page.get_by_test_id("btn-prev-period").click()
    page.get_by_test_id("current-period").wait_for(state="attached")
    page.get_by_test_id("btn-prev-period").click()
    page.get_by_test_id("current-period").wait_for(state="attached")
    
    # Should be in a different period than we started
    final_period = page.get_by_test_id("current-period").text_content()
    assert final_period != current_period


@pytest.mark.e2e
def test_empty_state_dashboard(page, live_server):
    """Test the empty state on dashboard when no entries exist."""
    page.goto(live_server)
    
    # Check for empty state
    empty_state = page.get_by_test_id("empty-entries")
    assert empty_state.is_visible()
    assert "No time entries found" in empty_state.text_content()


@pytest.mark.e2e
def test_empty_state_reports(page, live_server):
    """Test the empty state on reports when no entries exist."""
    page.goto(f"{live_server}/reports")
    
    # Check for empty state
    empty_state = page.get_by_test_id("empty-entries")
    assert empty_state.is_visible()
    assert "No time entries found" in empty_state.text_content()


@pytest.mark.e2e
def test_dashboard_quick_actions(page, live_server):
    """Test quick action links on dashboard."""
    page.goto(live_server)
    
    # Check that quick actions are visible
    assert page.get_by_test_id("action-add-time").is_visible()
    assert page.get_by_test_id("action-view-reports").is_visible()
    assert page.get_by_test_id("action-manage-leave").is_visible()
    
    # Click on view reports action
    page.get_by_test_id("action-view-reports").click()
    page.wait_for_url(f"{live_server}/reports*")
    assert page.get_by_test_id("reports-page").is_visible()


@pytest.mark.e2e
def test_complete_user_flow(page, live_server):
    """Test a complete user flow: add time entry, view in reports, and delete."""
    # Start at dashboard
    page.goto(live_server)
    
    # Navigate to add time entry
    page.get_by_test_id("nav-time-entry").click()
    page.wait_for_url(f"{live_server}/time-entry")
    
    # Add a time entry
    today = datetime.now().date().isoformat()
    page.get_by_test_id("input-date").fill(today)
    page.get_by_test_id("input-start-time").fill("08:00")
    page.get_by_test_id("input-end-time").fill("16:00")
    page.get_by_test_id("input-description").fill("Full day of work")
    page.get_by_test_id("btn-submit").click()
    
    # Should be redirected to dashboard with success message
    page.wait_for_url(live_server + "/")
    assert page.get_by_test_id("flash-success").is_visible()
    
    # Check dashboard stats updated
    weekly_hours = page.get_by_test_id("stat-weekly-hours")
    assert weekly_hours.is_visible()
    assert "8" in weekly_hours.text_content() or "8.0" in weekly_hours.text_content()
    
    # Navigate to reports
    page.get_by_test_id("nav-reports").click()
    page.wait_for_url(f"{live_server}/reports*")
    
    # Verify entry appears in reports
    entries_table = page.get_by_test_id("entries-table")
    assert entries_table.is_visible()
    assert "Full day of work" in entries_table.text_content()
    
    # Go back to dashboard
    page.get_by_test_id("nav-dashboard").click()
    page.wait_for_url(live_server + "/")
    
    # Delete the entry
    page.on("dialog", lambda dialog: dialog.accept())
    delete_button = page.locator('[data-testid^="btn-delete-entry-"]').first
    delete_button.click()
    
    # Wait for the success message to appear
    page.get_by_test_id("flash-success").wait_for(state="visible")
    
    # Verify deletion success
    assert page.get_by_test_id("flash-success").is_visible()
