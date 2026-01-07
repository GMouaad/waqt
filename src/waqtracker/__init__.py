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
    
    # Configuration - Database URI
    # Allow override via environment variable
    database_uri = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///time_tracker.db"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize database
    db.init_app(app)

    # Register routes
    with app.app_context():
        from . import routes

        app.register_blueprint(routes.bp)

        # Create tables if they don't exist
        db.create_all()

    return app
