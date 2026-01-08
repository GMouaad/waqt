"""Flask application factory and configuration."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

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
        print(
            "WARNING: Using default insecure SECRET_KEY. This is intended for development only. "
            "Set the SECRET_KEY environment variable for production deployments."
        )
    app.config["SECRET_KEY"] = secret_key
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception:
        pass
    
    # Configuration - Database URI
    # Default to instance folder for portability, with legacy support for root folder
    if not os.environ.get("SQLALCHEMY_DATABASE_URI"):
        db_path = os.path.join(app.instance_path, "time_tracker.db")
        # Legacy support: if it exists in root but not in instance, use root
        if not os.path.exists(db_path) and os.path.exists("time_tracker.db"):
            db_path = os.path.abspath("time_tracker.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    db.init_app(app)

    # Register routes
    with app.app_context():
        from . import routes
        from .utils import format_time

        app.register_blueprint(routes.bp)
        
        # Register Jinja filters
        @app.template_filter('format_time')
        def format_time_filter(time_obj):
            """Jinja filter to format time according to user settings."""
            return format_time(time_obj)

        # Create tables if they don't exist
        db.create_all()
        
        # Run migrations for existing databases
        try:
            # Add project root to sys.path to import migrations
            import sys
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from migrations.run_migrations import run_migrations
            # Pass the absolute path to ensure we're migrating the same file SQLAlchemy is using
            actual_db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
            run_migrations(actual_db_path)
        except ImportError:
            # If migrations folder is missing, we just skip it
            pass
        except Exception as e:
            app.logger.error(f"Failed to run migrations: {e}")

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
            existing = Settings.query.filter_by(key=key).first()
            if not existing:
                setting = Settings(key=key, value=value)
                db.session.add(setting)
                settings_changed = True
        
        if settings_changed:
            db.session.commit()

    return app
