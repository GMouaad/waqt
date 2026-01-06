# Migration Guide: From pip to uv

This guide helps you migrate from the traditional `pip` workflow to the modern, faster `uv` package manager.

## What is uv?

`uv` is an extremely fast Python package and project manager, written in Rust. It's designed as a drop-in replacement for `pip` and `pip-tools`, offering 10-100x faster performance while maintaining full compatibility with existing Python workflows.

### Key Benefits

- ⚡ **10-100x Faster**: Dramatically reduced installation times
- 🔒 **Better Dependency Resolution**: Automatic conflict resolution
- 📦 **Built-in Virtual Environment Management**: No need for separate `venv` commands
- 🚀 **Modern Tooling**: Single tool for all package management needs
- 🔄 **Fully Compatible**: Works with `requirements.txt` and `pyproject.toml`

## Installation

### Linux/macOS

```bash
# Recommended: Install via official script
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative: Install via pip
pip install uv
```

### Windows

```powershell
# Recommended: Install via PowerShell script
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Install via pip
pip install uv
```

### Verify Installation

```bash
uv --version
```

## Migration Steps

### For New Users (Clean Setup)

If you're starting fresh:

1. **Install uv** (see above)

2. **Clone the repository**:
   ```bash
   git clone https://github.com/GMouaad/time-tracker.git
   cd time-tracker
   ```

3. **Create virtual environment with uv**:
   ```bash
   uv venv
   ```
   This creates a `.venv` directory (note the dot prefix).

4. **Activate the environment**:
   ```bash
   # Linux/macOS
   source .venv/bin/activate
   
   # Windows
   .venv\Scripts\activate
   ```

5. **Install dependencies**:
   ```bash
   # Production dependencies only
   uv pip install -e .
   
   # With development dependencies
   uv pip install -e ".[dev]"
   ```

6. **Initialize database and run**:
   ```bash
   python init_db.py
   python run.py
   ```

### For Existing Users (Migrating)

If you have an existing `venv` directory:

1. **Install uv** (see installation section above)

2. **Back up your current environment** (optional but recommended):
   ```bash
   pip freeze > old_requirements_backup.txt
   ```

3. **Deactivate and remove old virtual environment**:
   ```bash
   deactivate
   rm -rf venv/  # Linux/macOS
   # or
   rmdir /s venv  # Windows
   ```

4. **Create new virtual environment with uv**:
   ```bash
   uv venv
   ```

5. **Activate new environment**:
   ```bash
   # Linux/macOS
   source .venv/bin/activate
   
   # Windows
   .venv\Scripts\activate
   ```

6. **Install dependencies**:
   ```bash
   # For development
   uv pip install -e ".[dev]"
   ```

7. **Verify everything works**:
   ```bash
   python init_db.py  # If you deleted the database
   pytest tests/ -v
   python run.py
   ```

## Quick Reference: Command Comparison

| Task | pip | uv |
|------|-----|-----|
| Create virtual environment | `python -m venv venv` | `uv venv` |
| Activate (Linux/macOS) | `source venv/bin/activate` | `source .venv/bin/activate` |
| Activate (Windows) | `venv\Scripts\activate` | `.venv\Scripts\activate` |
| Install project | `pip install -r requirements.txt` | `uv pip install -e .` |
| Install dev dependencies | `pip install -r requirements-dev.txt` | `uv pip install -e ".[dev]"` |
| Install package | `pip install package-name` | `uv pip install package-name` |
| Update package | `pip install --upgrade package-name` | `uv pip install --upgrade package-name` |
| List packages | `pip list` | `uv pip list` |
| Freeze dependencies | `pip freeze` | `uv pip freeze` |

## Using the Startup Scripts

The `start.sh` (Linux/macOS) and `start.bat` (Windows) scripts now automatically detect and use `uv` if available, with automatic fallback to `pip`.

### Linux/macOS

```bash
chmod +x start.sh
./start.sh
```

### Windows

```bash
start.bat
```

The scripts will:
1. Detect if `uv` is installed
2. Create virtual environment (`.venv` if using uv, `venv` if using pip)
3. Install dependencies
4. Initialize database (if needed)
5. Start the application

## Development Workflow with uv

### Adding New Dependencies

If you need to add a new package:

1. **Install the package**:
   ```bash
   uv pip install package-name
   ```

2. **Update pyproject.toml** to include the dependency in the `dependencies` list

3. **For dev dependencies**, add to the `[project.optional-dependencies]` section under `dev`

### Running Tests

```bash
# Make sure dev dependencies are installed
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src.waqtracker
```

### Code Formatting and Linting

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
```

## Troubleshooting

### uv command not found

**Solution**: Restart your terminal or manually add uv to your PATH:
```bash
# Linux/macOS - Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.cargo/bin:$PATH"

# Windows - The installer usually handles this automatically
# If not, add %USERPROFILE%\.cargo\bin to your PATH
```

### Virtual environment in wrong location

If you accidentally created `venv` instead of `.venv`:
```bash
deactivate
rm -rf venv
uv venv  # Creates .venv
```

### Dependency conflicts

uv has better dependency resolution than pip, but if you encounter issues:
```bash
# Clear cache
uv cache clean

# Try installation again
uv pip install -e ".[dev]"
```

### Want to switch back to pip?

No problem! The project still fully supports pip:
```bash
# Deactivate and remove uv environment
deactivate
rm -rf .venv

# Create traditional venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install with pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Performance Comparison

Based on typical installations of this project:

| Operation | pip | uv | Improvement |
|-----------|-----|-----|-------------|
| Fresh install | ~20-30s | ~2-3s | 10x faster |
| Reinstall (cached) | ~15-20s | ~0.5-1s | 20x faster |
| Add single package | ~5-10s | ~0.5-1s | 10x faster |

*Times are approximate and may vary based on network speed and system performance*

## Best Practices

1. **Use `.venv` for uv environments**: Distinguishes uv environments from traditional `venv` directories
2. **Keep both requirements.txt and pyproject.toml**: Maintains backward compatibility
3. **Update documentation**: If you add dependencies, update both files
4. **Test with both**: Before major releases, verify both pip and uv installations work
5. **CI/CD**: The GitHub Actions workflow now tests both methods

## Getting Help

- **uv documentation**: https://github.com/astral-sh/uv
- **Project issues**: https://github.com/GMouaad/time-tracker/issues
- **Python packaging guide**: https://packaging.python.org/

## Conclusion

Migrating to `uv` is straightforward and offers significant performance benefits. The project maintains full backward compatibility with `pip`, so you can switch back anytime. We recommend trying `uv` for development work where the faster iteration cycles make a real difference.

Happy coding! 🚀
