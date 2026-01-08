# Playwright E2E Testing Documentation

## Overview

This project includes comprehensive end-to-end (E2E) browser tests using Playwright. These tests verify that the web UI works correctly across all major user flows.

## Features

### ✅ Implemented Features

1. **Playwright Integration**: Full browser automation using `pytest-playwright`
2. **Robust Selectors**: All interactive elements have `data-testid` attributes for reliable test selectors
3. **Graceful Skipping**: Tests automatically skip (not fail) when Playwright browsers aren't installed
4. **CI/CD Integration**: GitHub Actions workflow installs browsers and runs tests automatically
5. **Comprehensive Coverage**: 13 E2E tests covering all major user flows

## Test Coverage

### Major User Flows Tested

- ✅ **Navigation**: Page loading and navigation between all sections
- ✅ **Time Entries**: Adding, viewing, and deleting time entries
- ✅ **Leave Management**: Adding vacation and sick leave days
- ✅ **Reports**: Week/month view toggling and period navigation
- ✅ **Empty States**: Proper display when no data exists
- ✅ **Form Validation**: Client-side validation of required fields
- ✅ **Complete Workflows**: End-to-end user journeys

## Running Tests

### Prerequisites

1. **Install Dependencies**:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. **Install Playwright Browsers** (required for E2E tests):
   ```bash
   playwright install chromium --with-deps
   ```

### Running E2E Tests

**Run all E2E tests:**
```bash
pytest tests/test_e2e.py -v
```

**Run a specific test:**
```bash
pytest tests/test_e2e.py::test_homepage_loads -v
```

**Run with more verbose output:**
```bash
pytest tests/test_e2e.py -vv --tb=short
```

### Running All Tests

**Run all tests (unit + E2E):**
```bash
pytest tests/ -v
```

**Run only E2E tests:**
```bash
pytest tests/ -v -m e2e
```

**Run excluding E2E tests:**
```bash
pytest tests/ -v -m "not e2e"
```

## Test Behavior

### When Playwright Browsers Are Installed

Tests run normally and execute browser automation:
```
tests/test_e2e.py::test_homepage_loads PASSED                    [  7%]
tests/test_e2e.py::test_navigation PASSED                        [ 15%]
...
=============== 13 passed in 19.38s ================
```

### When Playwright Browsers Are NOT Installed

Tests skip gracefully with a helpful message:
```
tests/test_e2e.py::test_homepage_loads SKIPPED (Playwright browsers not
installed - run 'playwright install' to enable E2E tests)                [  7%]
tests/test_e2e.py::test_navigation SKIPPED (Playwright browsers not
installed - run 'playwright install' to enable E2E tests)                [ 15%]
...
=============== 13 skipped in 0.02s ================
```

This ensures that:
- Local developers without Playwright installed don't get test failures
- CI/CD pipelines can run tests reliably
- Tests fail only when there are actual issues, not missing dependencies

## Data Test IDs

All interactive elements have `data-testid` attributes for reliable test selection:

### Navigation
- `navbar` - Main navigation bar
- `logo` - Waqt logo
- `nav-dashboard` - Dashboard navigation link
- `nav-time-entry` - Time Entry navigation link
- `nav-reports` - Reports navigation link
- `nav-leave` - Leave navigation link
- `theme-toggle` - Theme toggle button

### Dashboard
- `dashboard` - Main dashboard container
- `stat-weekly-hours` - Weekly hours stat card
- `stat-overtime` - Overtime stat card
- `stat-working-days` - Working days stat card
- `stat-standard-hours` - Standard hours stat card
- `btn-add-time-entry` - Add time entry button
- `recent-entries-table` - Recent entries table
- `entry-row-{id}` - Individual entry row
- `btn-delete-entry-{id}` - Delete entry button
- `empty-entries` - Empty state message
- `action-add-time` - Quick action: Add time
- `action-view-reports` - Quick action: View reports
- `action-manage-leave` - Quick action: Manage leave

### Time Entry Page
- `time-entry-page` - Time entry page container
- `time-entry-form` - Time entry form
- `input-date` - Date input field
- `input-start-time` - Start time input
- `input-end-time` - End time input
- `input-description` - Description textarea
- `btn-submit` - Submit button
- `btn-cancel` - Cancel button

### Reports Page
- `reports-page` - Reports page container
- `period-selector` - Period selector controls
- `btn-week-view` - Week view button
- `btn-month-view` - Month view button
- `date-navigator` - Date navigation controls
- `btn-prev-period` - Previous period button
- `btn-next-period` - Next period button
- `current-period` - Current period display
- `stat-total-hours` - Total hours stat
- `stat-overtime` - Overtime stat
- `stat-working-days` - Working days stat
- `stat-leave-days` - Leave days stat (month view only)
- `entries-table` - Time entries table
- `daily-summary-table` - Daily summary table
- `leave-days-table` - Leave days table
- `empty-entries` - Empty state message

### Leave Management Page
- `leave-page` - Leave page container
- `stat-vacation-days` - Vacation days stat
- `stat-sick-days` - Sick days stat
- `stat-total-leave` - Total leave stat
- `leave-form` - Leave form
- `input-leave-date` - Date input
- `select-leave-type` - Leave type selector
- `input-leave-description` - Description input
- `btn-add-leave` - Add leave button
- `leave-history-table` - Leave history table
- `leave-row-{id}` - Individual leave row
- `btn-delete-leave-{id}` - Delete leave button
- `empty-leave` - Empty state message

### Flash Messages
- `flash-messages` - Flash messages container
- `flash-success` - Success message
- `flash-error` - Error message

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/python-ci.yml`) automatically:

1. Installs Python dependencies including `pytest-playwright`
2. Installs Playwright chromium browser with system dependencies
3. Runs all tests including E2E tests
4. Reports test results

### Workflow Steps

```yaml
- name: Install dependencies
  run: |
    uv pip install -e ".[dev]"

- name: Install Playwright browsers
  run: |
    playwright install chromium --with-deps

- name: Run tests
  run: |
    pytest tests/ -v --tb=short
```

## Test Structure

### Fixtures (tests/conftest.py)

- `app`: Creates a test Flask application with a temporary SQLite database file
- `live_server`: Starts a live Flask server on a random port for E2E tests
- `browser_instance`: Creates a Playwright browser instance
- `page`: Creates a new browser page for each test

### Test Organization

Tests are organized by functionality:
- **Navigation tests**: Verify page loading and navigation
- **Form tests**: Test form submission and validation
- **CRUD tests**: Test create, read, update, delete operations
- **UI state tests**: Test empty states and conditional rendering
- **Integration tests**: Test complete user workflows

## Best Practices

### Writing New E2E Tests

1. **Use data-testid for selectors**:
   ```python
   page.get_by_test_id("btn-submit").click()
   ```

2. **Wait for navigation**:
   ```python
   page.wait_for_url(f"{live_server}/expected-path")
   ```

3. **Mark tests with @pytest.mark.e2e**:
   ```python
   @pytest.mark.e2e
   def test_new_feature(page, live_server):
       # test code
   ```

4. **Handle dialogs properly**:
   ```python
   page.on("dialog", lambda dialog: dialog.accept())
   ```

5. **Use appropriate waits**:
   ```python
   page.wait_for_timeout(500)  # for animations
   page.wait_for_selector('[data-testid="element"]')
   ```

### Adding New data-testid Attributes

When adding new interactive elements to the UI:

1. Add a descriptive `data-testid` attribute:
   ```html
   <button data-testid="btn-save">Save</button>
   ```

2. Use consistent naming conventions:
   - `btn-{action}` for buttons
   - `input-{field}` for inputs
   - `{element}-{descriptor}` for other elements

3. Document the new test ID in this file

## Troubleshooting

### Tests Skip Instead of Running

**Problem**: E2E tests show as SKIPPED
```
tests/test_e2e.py::test_homepage_loads SKIPPED
```

**Solution**: Install Playwright browsers
```bash
playwright install chromium
```

### Browser Launch Errors

**Problem**: `Error: BrowserType.launch: Executable doesn't exist`

**Solution**: Install browsers with system dependencies
```bash
playwright install chromium --with-deps
```

### Port Already in Use

**Problem**: Tests fail with "Address already in use"

**Solution**: The `live_server` fixture uses a random available port. This error is rare but can happen if you run tests in parallel. Run tests sequentially.

### Timeouts

**Problem**: Tests timeout waiting for elements

**Solution**: 
1. Increase timeout: `page.wait_for_timeout(5000)`
2. Check selector: Verify the `data-testid` exists
3. Check server: Ensure Flask app started correctly

## Maintenance

### Updating Tests

When the UI changes:
1. Update `data-testid` attributes in HTML templates if elements change
2. Update test assertions if expected content changes
3. Add new tests for new features
4. Run full test suite to verify no regressions

### Test Performance

Current E2E test execution time: ~18-20 seconds for 13 tests

Optimization tips:
- Keep tests focused and minimal
- Avoid unnecessary waits
- Reuse browser instances when possible (using fixtures)
- Run tests in parallel (future enhancement)

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [pytest-playwright Plugin](https://github.com/microsoft/playwright-pytest)
- [pytest Documentation](https://docs.pytest.org/)
