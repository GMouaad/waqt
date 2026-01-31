"""Seed the database with sample data for manual testing."""

from datetime import datetime, timedelta, time
import random
from waqt import create_app, db
from waqt.models import Category, TimeEntry, LeaveDay, Settings, Template


def seed_database(app=None):
    """Populate the database with sample data."""
    if app is None:
        app = create_app()

    with app.app_context():
        print("🌱 Starting database seeding...")

        # 1. Seed Categories
        categories_data = [
            {
                "name": "Development",
                "code": "DEV",
                "color": "#3b82f6",
                "description": "Coding and technical tasks",
            },
            {
                "name": "Meetings",
                "code": "MEET",
                "color": "#ef4444",
                "description": "Team syncs and client meetings",
            },
            {
                "name": "Planning",
                "code": "PLAN",
                "color": "#10b981",
                "description": "Sprint planning and roadmapping",
            },
            {
                "name": "Research",
                "code": "R&D",
                "color": "#8b5cf6",
                "description": "Learning and investigation",
            },
            {
                "name": "Admin",
                "code": "ADM",
                "color": "#6b7280",
                "description": "Emails and administrative work",
            },
        ]

        categories_map = {}  # name -> id

        print("\n--- Categories ---")
        for cat_data in categories_data:
            existing = Category.query.filter_by(name=cat_data["name"]).first()
            if not existing:
                category = Category(**cat_data)
                db.session.add(category)
                db.session.flush()  # Flush to get ID
                print(f"✓ Created category: {cat_data['name']}")
                categories_map[cat_data["name"]] = category.id
            else:
                print(f"• Skipped category: {cat_data['name']} (exists)")
                categories_map[cat_data["name"]] = existing.id

        # 2. Seed Settings (ensure defaults exist)
        print("\n--- Settings ---")
        default_settings = [
            ("standard_hours_per_day", "8"),
            ("weekly_hours", "40"),
            ("pause_duration_minutes", "45"),
        ]
        for key, value in default_settings:
            existing = Settings.query.filter_by(key=key).first()
            if not existing:
                setting = Settings(key=key, value=value)
                db.session.add(setting)
                print(f"✓ Added setting: {key}")
            else:
                pass  # Silent skip

        # 3. Seed Leave Days (Some in past, some in future)
        print("\n--- Leave Days ---")
        today = datetime.now().date()
        leave_data = [
            {
                "date": today - timedelta(days=20),
                "leave_type": "sick",
                "description": "Flu",
            },
            {
                "date": today + timedelta(days=10),
                "leave_type": "vacation",
                "description": "Long weekend",
            },
        ]

        for leave in leave_data:
            existing = LeaveDay.query.filter_by(date=leave["date"]).first()
            if not existing:
                leave_day = LeaveDay(**leave)
                db.session.add(leave_day)
                print(f"✓ Created {leave['leave_type']} leave on {leave['date']}")
            else:
                print(f"• Skipped leave on {leave['date']} (exists)")

        # 4. Seed Time Entries (Last 2 weeks)
        print("\n--- Time Entries ---")

        # Helper to check overlap or duplicate roughly
        def entry_exists(date_obj, start_t):
            return (
                TimeEntry.query.filter_by(date=date_obj, start_time=start_t).first()
                is not None
            )

        # Generate entries for the last 10 workdays
        entries_created = 0
        for i in range(14):  # Look back 2 weeks
            date_obj = today - timedelta(days=i)

            # Skip weekends (simple check, though app handles it,
            # usually we don't log work on weekends for seed)
            if date_obj.weekday() >= 5:
                continue

            # Skip if it matches our seeded leave dates
            if any(leave["date"] == date_obj for leave in leave_data):
                continue

            # Create a standard day: 9:00 - 17:00 with a break
            # Morning block: 09:00 - 12:30
            start_1 = time(9, 0)
            if not entry_exists(date_obj, start_1):
                # Randomize slightly
                if random.random() > 0.8:  # Occasional variation
                    desc = "Morning Sync"
                    cat_id = categories_map.get("Meetings")
                else:
                    desc = "Core Development"
                    cat_id = categories_map.get("Development")

                entry1 = TimeEntry(
                    date=date_obj,
                    start_time=start_1,
                    end_time=time(12, 30),
                    duration_hours=3.5,
                    description=desc,
                    category_id=cat_id,
                    is_active=False,
                )
                db.session.add(entry1)
                entries_created += 1

            # Afternoon block: 13:15 - 17:30
            start_2 = time(13, 15)
            if not entry_exists(date_obj, start_2):
                if random.random() > 0.7:
                    desc = "Project Planning"
                    cat_id = categories_map.get("Planning")
                elif random.random() > 0.5:
                    desc = "Code Review"
                    cat_id = categories_map.get("Development")
                else:
                    desc = "Documentation"
                    cat_id = categories_map.get("Admin")

                entry2 = TimeEntry(
                    date=date_obj,
                    start_time=start_2,
                    end_time=time(17, 30),
                    duration_hours=4.25,
                    description=desc,
                    category_id=cat_id,
                    is_active=False,
                )
                db.session.add(entry2)
                entries_created += 1

        if entries_created > 0:
            print(f"✓ Created {entries_created} time entries")
        else:
            print("• Skipped time entries (already populated)")

        # 5. Seed Templates
        print("\n--- Templates ---")
        templates_data = [
            {
                "name": "Standard Day",
                "start_time": time(9, 0),
                "duration_minutes": 480,
                "description": "Standard 8-hour work day",
                "category_id": categories_map.get("Development"),
                "pause_mode": "default",
                "is_default": True,
            },
            {
                "name": "Morning Standup",
                "start_time": time(9, 30),
                "duration_minutes": 30,
                "description": "Daily team synchronization",
                "category_id": categories_map.get("Meetings"),
                "pause_mode": "none",
                "is_default": False,
            },
            {
                "name": "Deep Work Session",
                "start_time": time(14, 0),
                "duration_minutes": 120,
                "description": "Focused coding session",
                "category_id": categories_map.get("Development"),
                "pause_mode": "custom",
                "pause_minutes": 10,
                "is_default": False,
            },
        ]

        for t_data in templates_data:
            existing = Template.query.filter_by(name=t_data["name"]).first()
            if not existing:
                template = Template(**t_data)
                db.session.add(template)
                print(f"✓ Created template: {t_data['name']}")
            else:
                print(f"• Skipped template: {t_data['name']} (exists)")

        db.session.commit()
        print("\n✅ Database seeding complete!")


if __name__ == "__main__":
    seed_database()
