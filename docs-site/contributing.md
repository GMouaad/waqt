# Contributing to Waqt

Thank you for your interest in contributing to the Waqt application!

📚 **For complete documentation, visit [https://gmouaad.github.io/waqt/](https://gmouaad.github.io/waqt/)**

## Development Setup

### Recommended: Using uv

The fastest and most modern way to set up the development environment:

1. **Install uv**
   ```bash
   # Recommended: Install via pip
   pip install uv
   
   # Alternative: Install via script (Linux/macOS)
   # For security, review https://astral.sh/uv/install.sh before running
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Alternative: Install via script (Windows PowerShell)
   # For security, review https://astral.sh/uv/install.ps1 before running
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/waqt.git
   cd waqt
   ```

3. **Create Virtual Environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install Dependencies (including dev dependencies)**
   ```bash
   uv pip install -e ".[dev]"
   ```

5. **Initialize Database**
   ```bash
   python -m waqtracker.scripts.init_db
   ```

6. **Run the Application**
   ```bash
   python -m waqtracker.wsgi
   ```

### Legacy: Using pip (Deprecated)

> **⚠️ DEPRECATED**: Consider using `uv` for better performance.

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/waqt.git
   cd waqt
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Initialize Database**
   ```bash
   python -m waqtracker.scripts.init_db
   ```

5. **Run the Application**
   ```bash
   python -m waqtracker.wsgi
   ```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=src.waqtracker  # With coverage report
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
   flake8 src/waqtracker/ tests/
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push to your fork and create a Pull Request

## Project Structure

- `src/waqtracker/` - Main application code
  - `__init__.py` - Flask app factory
  - `models.py` - Database models
  - `routes.py` - Route handlers
  - `utils.py` - Helper functions
  - `wsgi.py` - Application entry point
  - `scripts/` - Utility scripts (init_db, etc.)
  - `templates/` - HTML templates
  - `static/` - CSS, JS, images
- `tests/` - Test files

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
