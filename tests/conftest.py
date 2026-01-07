"""Pytest configuration and fixtures for the time tracker tests."""

import pytest
import os
import tempfile
from pathlib import Path

# Try to import playwright, but don't fail if it's not installed
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    
    # Check if browsers are installed by trying to launch Chromium via Playwright.
    # This relies on Playwright's own cross-platform browser detection instead of
    # hardcoding platform-specific installation paths.
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
            PLAYWRIGHT_BROWSERS_INSTALLED = True
    except Exception:
        PLAYWRIGHT_BROWSERS_INSTALLED = False
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PLAYWRIGHT_BROWSERS_INSTALLED = False


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", 
        "e2e: marks tests as end-to-end browser tests (requires Playwright)"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip e2e tests if Playwright is not available or browsers not installed."""
    if PLAYWRIGHT_AVAILABLE and PLAYWRIGHT_BROWSERS_INSTALLED:
        return
    
    skip_reason = (
        "Playwright not installed - skipping E2E tests" 
        if not PLAYWRIGHT_AVAILABLE 
        else "Playwright browsers not installed - run 'playwright install' to enable E2E tests"
    )
    skip_e2e = pytest.mark.skip(reason=skip_reason)
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


@pytest.fixture(scope="function")
def live_server(app):
    """Start a live Flask server for E2E tests."""
    if not PLAYWRIGHT_AVAILABLE or not PLAYWRIGHT_BROWSERS_INSTALLED:
        pytest.skip("Playwright not available or browsers not installed")
    
    from werkzeug.serving import make_server
    import threading
    
    # Use a random available port
    server = make_server("127.0.0.1", 0, app)
    port = server.port
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    # Return the base URL
    yield f"http://127.0.0.1:{port}"
    
    server.shutdown()


@pytest.fixture(scope="function")
def app():
    """Create a test Flask application instance."""
    from src.waqtracker import create_app, db
    
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    # Clean up the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def browser_instance():
    """Create a browser instance for tests."""
    if not PLAYWRIGHT_AVAILABLE or not PLAYWRIGHT_BROWSERS_INSTALLED:
        pytest.skip("Playwright not available or browsers not installed")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser_instance):
    """Create a new page for each test."""
    if not PLAYWRIGHT_AVAILABLE or not PLAYWRIGHT_BROWSERS_INSTALLED:
        pytest.skip("Playwright not available or browsers not installed")
    
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 720}
    )
    page = context.new_page()
    yield page
    context.close()
