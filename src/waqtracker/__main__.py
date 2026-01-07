"""Main entry point for waqtracker application.

This module serves as the entry point when running waqtracker as a package
or as a PyInstaller executable. It provides both CLI and web app functionality.
"""

import sys
import os

# Handle both package and frozen execution
if getattr(sys, 'frozen', False):
    # Running as frozen executable (PyInstaller)
    from waqtracker import create_app
    from waqtracker.cli import cli
else:
    # Running as package
    from . import create_app
    from .cli import cli


def main():
    """Main entry point that determines whether to run CLI or web app."""
    # If no arguments or only --help/--version, show combined help
    if len(sys.argv) == 1:
        # Determine appropriate CLI invocation name
        if getattr(sys, "frozen", False):
            cli_name = os.path.basename(sys.executable)
        else:
            cli_name = "waqt"
        
        # No arguments - start the web application
        port = int(os.environ.get("PORT", 5555))
        print("Starting waqtracker web application...")
        print(f"Access the application at: http://localhost:{port}")
        print("\nPress Ctrl+C to stop the server.")
        print(f"\nTo use the CLI, run: {cli_name} <command>")
        print(f"For CLI help, run: {cli_name} --help")
        print("-" * 50)
        
        try:
            app = create_app()
            debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
            # Bind to localhost only for security (prevents external access)
            app.run(debug=debug_mode, host="127.0.0.1", port=port)
        except Exception as e:
            print(f"\n❌ Error starting application: {e}", file=sys.stderr)
            print("\nPlease check that:")
            print(f"  - Port {port} is not already in use")
            print("  - You have write permissions in the current directory")
            print("  - All required dependencies are available")
            sys.exit(1)
    else:
        # Arguments provided - run CLI
        cli()


if __name__ == "__main__":
    main()
