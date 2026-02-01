"""WSGI server script for background execution.

This script is invoked by the process manager to run the Flask server
as a detached background process. It uses Waitress as a production-ready
WSGI server instead of Flask's development server.
"""

import argparse
import sys


def main():
    """Run the Flask application with Waitress production server."""
    parser = argparse.ArgumentParser(description="Waqt WSGI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5555, help="Port to bind to")
    args = parser.parse_args()

    # Import app factory
    from waqt import create_app

    app = create_app()

    # Use Waitress production server
    from waitress import serve

    print(f"Waqt server starting on http://{args.host}:{args.port}")
    serve(app, host=args.host, port=args.port, threads=4)


if __name__ == "__main__":
    sys.exit(main() or 0)
