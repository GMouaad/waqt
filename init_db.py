"""Initialize the database and create default settings."""
from src.waqtracker import create_app, db
from src.waqtracker.models import Settings

def init_database():
    """Initialize the database with tables and default settings."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Add default settings if they don't exist
        default_settings = [
            ('standard_hours_per_day', '8'),
            ('standard_hours_per_week', '40'),
        ]
        
        for key, value in default_settings:
            existing = Settings.query.filter_by(key=key).first()
            if not existing:
                setting = Settings(key=key, value=value)
                db.session.add(setting)
                print(f"✓ Added setting: {key} = {value}")
        
        db.session.commit()
        print("\n✅ Database initialization complete!")
        print("You can now run the app with: python run.py")

if __name__ == '__main__':
    init_database()
