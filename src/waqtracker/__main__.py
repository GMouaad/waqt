"""Main entry point for waqtracker application.

This module serves as the entry point when running waqtracker as a package
or as a PyInstaller executable. It provides both CLI and web app functionality.
"""

import sys
import os
from . import create_app
from .cli import cli


def main():
    """Main entry point that determines whether to run CLI or web app."""
    # If no arguments or only --help/--version, show combined help
    if len(sys.argv) == 1:
        # No arguments - start the web application
        print("Starting waqtracker web application...")
        print("Access the application at: http://localhost:5000")
        print("\nPress Ctrl+C to stop the server.")
        print("\nTo use the CLI, run: waqt <command>")
        print("For CLI help, run: waqt --help")
        print("-" * 50)
        
        app = create_app()
        debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
        app.run(debug=debug_mode, host="0.0.0.0", port=5000)
    else:
        # Arguments provided - run CLI
        cli()


if __name__ == "__main__":
    main()
