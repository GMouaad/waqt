# Contributing to Time Tracker

Thank you for your interest in contributing to the Time Tracker application!

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/time-tracker.git
   cd time-tracker
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

4. **Initialize Database**
   ```bash
   python init_db.py
   ```

5. **Run the Application**
   ```bash
   python run.py
   ```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app  # With coverage report
```

## Code Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

## Making Changes

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test thoroughly

3. Run linting:
   ```bash
   flake8 app/ tests/
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push to your fork and create a Pull Request

## Project Structure

- `app/` - Main application code
  - `__init__.py` - Flask app factory
  - `models.py` - Database models
  - `routes.py` - Route handlers
  - `utils.py` - Helper functions
  - `templates/` - HTML templates
  - `static/` - CSS, JS, images
- `tests/` - Test files
- `run.py` - Application entry point
- `init_db.py` - Database initialization

## Features to Contribute

- Export data to CSV/Excel
- Calendar view of time entries
- Charts and visualizations
- Dark mode support
- Multi-user support
- API endpoints
- Mobile app
- Desktop notifications

## Questions?

Open an issue on GitHub for any questions or discussions!
