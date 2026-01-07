"""Main entry point for the Waqt application."""

from waqtracker import create_app
import os

app = create_app()

if __name__ == "__main__":
    # WARNING: This is a development server. Do not use it in production.
    # For production, use a WSGI server like Gunicorn or uWSGI with debug=False.
    # Running with debug=True on 0.0.0.0 exposes the debugger to the network
    # and can leak sensitive information.
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    port = int(os.environ.get("PORT", 5555))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
