#!/usr/bin/env python3
"""
Demonstration script for the Waqtracker MCP Server.

This script shows how to interact with the MCP server programmatically
by calling the tools directly. In production, these would be called
through the MCP protocol by an MCP client.
"""

import os
import tempfile

from src.waqtracker import create_app, db
from src.waqtracker.mcp_server import (
    start,
    end,
    summary,
    list_entries,
    export_entries,
)
import json


def print_result(title, result):
    """Pretty print a result."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(json.dumps(result, indent=2))


def main():
    """Demonstrate MCP server functionality."""
    print("\n" + "=" * 60)
    print("  Waqtracker MCP Server Demonstration")
    print("=" * 60)
    
    # Use a temporary database for the demo
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    os.environ['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{temp_db.name}'
    
    # Initialize the database
    app = create_app()
    with app.app_context():
        db.create_all()
    
    print(f"\n✓ Database initialized (using temporary file: {temp_db.name})")
    
    # Demonstration workflow
    print("\n--- Workflow: Complete Time Tracking Session ---")
    
    # 1. Start time tracking
    result = start(time="09:00", description="MCP Demo Session")
    print_result("1. Start Time Tracking", result)
    
    # 2. End time tracking
    result = end(time="17:00")
    print_result("2. End Time Tracking", result)
    
    # 3. Get weekly summary
    result = summary(period="week")
    print_result("3. Weekly Summary", result)
    
    # 4. List all entries
    result = list_entries(period="all", limit=5)
    print_result("4. List Entries", result)
    
    # 5. Export to CSV
    result = export_entries(period="week")
    # Only show metadata, not the full CSV content
    export_summary = {k: v for k, v in result.items() if k != "csv_content"}
    export_summary["csv_content"] = f"<{len(result['csv_content'])} bytes>"
    print_result("5. Export to CSV", export_summary)
    
    print("\n" + "=" * 60)
    print("  Demonstration Complete!")
    print("=" * 60)
    print("\nAll MCP tools executed successfully.")
    print("In production, these would be called via MCP protocol by AI assistants.")
    print(f"\nCleaning up temporary database: {temp_db.name}\n")
    
    # Clean up
    os.unlink(temp_db.name)


if __name__ == "__main__":
    main()
