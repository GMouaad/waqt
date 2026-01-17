import pytest
from datetime import date, time
from src.waqt import create_app, db
from src.waqt.models import Category, TimeEntry

@pytest.fixture
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def init_db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()

def test_category_model(init_db):
    cat = Category(name="Development", code="DEV", color="#000000")
    db.session.add(cat)
    db.session.commit()
    
    assert cat.id is not None
    assert cat.name == "Development"

def test_create_category(client, init_db):
    response = client.post('/categories', data={
        'name': 'Meeting',
        'code': 'MEET',
        'color': '#ff0000'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Category added successfully!" in response.data
    
    with client.application.app_context():
        cat = Category.query.first()
        assert cat.name == 'Meeting'
        assert cat.code == 'MEET'

def test_time_entry_with_category(client, init_db):
    # Create category
    with client.application.app_context():
        cat = Category(name="Dev")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
    
    # Add entry with category
    response = client.post('/time-entry', data={
        'date': '2023-01-01',
        'start_time': '09:00',
        'end_time': '10:00',
        'description': 'Coding',
        'category_id': str(cat_id)
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Time entry added successfully" in response.data
    
    with client.application.app_context():
        entry = TimeEntry.query.first()
        assert entry.category_id == cat_id
        assert entry.category.name == "Dev"

def test_edit_category(client, init_db):
    with client.application.app_context():
        cat = Category(name="Old Name")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
    
    response = client.post(f'/categories/{cat_id}/edit', data={
        'name': 'New Name',
        'code': 'NEW',
        'color': '#00ff00'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Category updated successfully" in response.data
    
    with client.application.app_context():
        updated_cat = db.session.get(Category, cat_id)
        assert updated_cat.name == "New Name"

def test_delete_category(client, init_db):
    with client.application.app_context():
        cat = Category(name="To Delete")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
    
    response = client.post(f'/categories/{cat_id}/delete', follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Category deleted successfully" in response.data
    
    with client.application.app_context():
        assert Category.query.count() == 0

def test_delete_category_in_use_fails(client, init_db):
    with client.application.app_context():
        cat = Category(name="In Use")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
        
        entry = TimeEntry(
            date=date(2023, 1, 1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            duration_hours=1.0,
            description="Work",
            category_id=cat.id
        )
        db.session.add(entry)
        db.session.commit()
    
    response = client.post(f'/categories/{cat_id}/delete', follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Cannot delete category currently assigned" in response.data
    
    with client.application.app_context():
        assert Category.query.count() == 1

def test_category_color_validation(client, init_db):
    # Test invalid color
    response = client.post('/categories', data={
        'name': 'Bad Color',
        'color': 'invalid'
    }, follow_redirects=True)
    assert b"Color must be a valid hex code" in response.data
    
    # Test invalid hex
    response = client.post('/categories', data={
        'name': 'Bad Hex',
        'color': '#GGGGGG'
    }, follow_redirects=True)
    assert b"Color must be a valid hex code" in response.data
    
    # Test valid hex
    response = client.post('/categories', data={
        'name': 'Good Color',
        'color': '#FF0000'
    }, follow_redirects=True)
    assert b"Category added successfully" in response.data
