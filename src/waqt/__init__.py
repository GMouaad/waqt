"""Flask application factory and configuration."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys

from .database import Base, init_engine, get_database_path, run_migrations
from .logging import get_flask_logger

# Create Flask-SQLAlchemy instance that shares the Base metadata
db = SQLAlchemy(model_class=Base)


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Initialize logging
    logger = get_flask_logger()
    logger.info("Starting Flask application")

    # Configuration - Secret Key
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        is_production = (
            os.environ.get("FLASK_ENV") == "production"
            or os.environ.get("ENV") == "production"
        )
        if is_production:
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production."
            )
        secret_key = "dev-secret-key-change-in-production"
        # Warning will be visible in development
        if not test_config:
            print(
                "WARNING: Using default insecure SECRET_KEY. This is intended for development only. "
                "Set the SECRET_KEY environment variable for production deployments."
            )
    app.config["SECRET_KEY"] = secret_key

    if test_config:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Determine database path from shared database module
    if test_config and "SQLALCHEMY_DATABASE_URI" in test_config:
        # Use test config URI
        database_url = test_config["SQLALCHEMY_DATABASE_URI"]
    elif os.environ.get("SQLALCHEMY_DATABASE_URI"):
        database_url = os.environ.get("SQLALCHEMY_DATABASE_URI")
    else:
        db_path = get_database_path()
        database_url = f"sqlite:///{db_path}"
        # Store the data dir in config for other uses if needed
        app.config["DATA_DIR"] = os.path.dirname(db_path)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize the shared SQLAlchemy engine for non-Flask contexts
    init_engine(database_url)

    # Initialize Flask-SQLAlchemy
    db.init_app(app)

    # Register routes
    with app.app_context():
        from . import routes
        from .utils import format_time

        app.register_blueprint(routes.bp)

        # Register Jinja filters
        @app.template_filter("format_time")
        def format_time_filter(time_obj):
            """Jinja filter to format time according to user settings."""
            return format_time(time_obj)

        # Create tables if they don't exist
        db.create_all()

        # Run migrations for existing databases
        actual_db_path = database_url.replace("sqlite:///", "")
        run_migrations(actual_db_path)

        # Seed default settings if they don't exist
        from .models import Settings

        default_settings = [
            ("standard_hours_per_day", "8"),
            ("weekly_hours", "40"),
            ("pause_duration_minutes", "45"),
            ("auto_end", "false"),
        ]

        settings_changed = False
        for key, value in default_settings:
            existing = db.session.query(Settings).filter_by(key=key).first()
            if not existing:
                setting = Settings(key=key, value=value)
                db.session.add(setting)
                settings_changed = True

        if settings_changed:
            db.session.commit()

    return app
