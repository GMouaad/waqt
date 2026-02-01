"""WSGI server script for background execution.

This script is invoked by the process manager to run the Flask server
as a detached background process. It should not be run directly by users.
"""

import argparse
import sys


def main():
    """Run the Flask application server."""
    parser = argparse.ArgumentParser(description="Waqt WSGI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5555, help="Port to bind to")
    args = parser.parse_args()

    # Import app factory
    from waqt import create_app

    app = create_app()

    # Run with reloader disabled (important for background execution)
    app.run(
        host=args.host,
        port=args.port,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
