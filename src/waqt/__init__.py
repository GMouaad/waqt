"""Flask application factory and configuration."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import shutil
import sys
import platformdirs

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
    
    # Determine data directory
    # Priority:
    # 1. WAQT_DATA_DIR environment variable
    # 2. Platform-specific user data directory (platformdirs)
    custom_data_dir = os.environ.get("WAQT_DATA_DIR")
    if custom_data_dir:
        data_dir = os.path.abspath(custom_data_dir)
    else:
        # Use "waqt" as app name and "GMouaad" as app author (matches repo)
        data_dir = platformdirs.user_data_dir("waqt", "GMouaad")
    
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create data directory {data_dir}: {e}")
        # Fallback to instance path if system permission issues
        data_dir = app.instance_path
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            print(
                f"Warning: Could not create fallback data directory {data_dir}: {e}"
            )

    # Configuration - Database URI
    if not os.environ.get("SQLALCHEMY_DATABASE_URI"):
        db_filename = "time_tracker.db"
        db_path = os.path.join(data_dir, db_filename)
        
        # Migration logic: Check for existing DB in legacy locations if not found in new location
        if not os.path.exists(db_path):
            legacy_candidates = [
                # 1. Instance folder (standard Flask)
                os.path.join(app.instance_path, db_filename),
                # 2. Current working directory (common legacy behavior)
                os.path.abspath(db_filename),
                # 3. Instance folder in CWD
                os.path.abspath(os.path.join("instance", db_filename))
            ]
            
            # If running as PyInstaller executable, check next to executable
            if getattr(sys, 'frozen', False):
                 # sys.executable points to the binary
                 exe_dir = os.path.dirname(sys.executable)
                 legacy_candidates.append(os.path.join(exe_dir, db_filename))
                 legacy_candidates.append(os.path.join(exe_dir, "instance", db_filename))

            for legacy_path in legacy_candidates:
                if os.path.exists(legacy_path) and os.path.isfile(legacy_path):
                    try:
                        print(f"Migrating database from {legacy_path} to {db_path}...")
                        shutil.copy2(legacy_path, db_path)
                        print("Migration successful.")
                        break
                    except Exception as e:
                        print(f"Error migrating database from {legacy_path}: {e}")

        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        # Store the data dir in config for other uses if needed
        app.config["DATA_DIR"] = data_dir
        # Only print in dev/verbose mode ideally, but useful for debugging now
        # print(f"Using database at: {db_path}")

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
