# MCP Server Documentation

## Overview

The Waqt MCP (Model Context Protocol) server exposes time tracking functionality to LLM applications and AI assistants. It provides the same core features as the CLI interface, allowing AI tools to track work hours, generate reports, and manage time entries.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). The Waqt MCP server implements this protocol, making time tracking functionality available to any MCP-compatible AI assistant.

## Installation

The MCP server is included with the Waqt package. After installing Waqt:

```bash
# Install waqt with MCP support
uv pip install -e .

# Or using pip (legacy)
pip install -e .
```

The `waqt-mcp` command will be available after installation.

## Running the MCP Server

### Starting the Server

The MCP server runs in stdio mode, which is the standard transport for MCP:

**Using uv (Recommended):**
```bash
uv run waqt-mcp
```

**Using activated environment:**
```bash
waqt-mcp
```

The server will start and listen for MCP protocol messages on stdin/stdout.

### Using with MCP Clients

To use the Waqt MCP server with an MCP-compatible client, you'll need to configure the client to connect to the server. Here's an example configuration for Claude Desktop:

**Claude Desktop Configuration** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "waqt": {
      "command": "uv",
      "args": ["run", "waqt-mcp"],
      "env": {}
    }
  }
}
```

**Note:** If using the legacy installation method, replace `command` with `waqt-mcp` and remove `args`.

**Using with other MCP clients:**

For other MCP clients, refer to their documentation for how to configure stdio-based MCP servers.

## Available Tools

The MCP server exposes the following tools that mirror CLI functionality:

### 1. start

Start time tracking for a day.

**Parameters:**
- `time` (optional): Start time in HH:MM format (e.g., "09:00"). Defaults to current time.
- `date` (optional): Date in YYYY-MM-DD format (e.g., "2024-01-15"). Defaults to today.
- `description` (optional): Description of the work session. Defaults to "Work session".

**Returns:** JSON object with status, message, and entry details.

**Example:**
```json
{
  "time": "09:00",
  "date": "2024-01-15",
  "description": "Morning work session"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Time tracking started!",
  "entry": {
    "date": "2024-01-15",
    "start_time": "09:00",
    "description": "Morning work session"
  }
}
```

### 2. end

End time tracking for a day.

**Parameters:**
- `time` (optional): End time in HH:MM format (e.g., "17:30"). Defaults to current time.
- `date` (optional): Date in YYYY-MM-DD format (e.g., "2024-01-15"). Defaults to today.

**Returns:** JSON object with status, message, and entry details including calculated duration.

**Example:**
```json
{
  "time": "17:30",
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Time tracking ended!",
  "entry": {
    "date": "2024-01-15",
    "start_time": "09:00",
    "end_time": "17:30",
    "duration": "8:30",
    "duration_hours": 8.5,
    "description": "Morning work session"
  }
}
```

### 3. summary

Get time summary for a week or month.

**Parameters:**
- `period` (optional): "week" or "month". Defaults to "week".
- `date` (optional): Reference date in YYYY-MM-DD format. Defaults to today.

**Returns:** JSON object with period information, statistics, and recent entries.

**Example:**
```json
{
  "period": "week",
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "status": "success",
  "period": "Week",
  "start_date": "2024-01-15",
  "end_date": "2024-01-21",
  "statistics": {
    "total_hours": 40.0,
    "total_hours_formatted": "40:00",
    "working_days": 5,
    "overtime": 0.0,
    "overtime_formatted": "0:00",
    "standard_hours": 40.0
  },
  "recent_entries": [...],
  "has_entries": true
}
```

### 4. list_entries

List time entries for a specified period.

**Parameters:**
- `period` (optional): "week", "month", or "all". Defaults to "week".
- `date` (optional): Reference date in YYYY-MM-DD format. Defaults to today.
- `limit` (optional): Maximum number of entries to return. If not specified, returns all.

**Returns:** JSON object with entries list and metadata.

**Example:**
```json
{
  "period": "week",
  "limit": 10
}
```

**Response:**
```json
{
  "status": "success",
  "period": "week",
  "count": 5,
  "start_date": "2024-01-15",
  "end_date": "2024-01-21",
  "entries": [
    {
      "id": 1,
      "date": "2024-01-15",
      "day_of_week": "Monday",
      "start_time": "09:00",
      "end_time": "17:00",
      "duration": "8:00",
      "duration_hours": 8.0,
      "description": "Work session",
      "is_open": false,
      "created_at": "2024-01-15T09:00:00"
    }
  ]
}
```

### 5. export_entries

Export time entries to CSV format.

**Parameters:**
- `period` (optional): "week", "month", or "all". Defaults to "all".
- `date` (optional): Reference date in YYYY-MM-DD format. Defaults to today.
- `format` (optional): Export format, currently only "csv" is supported. Defaults to "csv".

**Returns:** JSON object with CSV content as a string and metadata.

**Example:**
```json
{
  "period": "month",
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Export successful!",
  "count": 20,
  "total_hours": 160.0,
  "total_hours_formatted": "160:00",
  "period": "month_2024-01",
  "format": "csv",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "csv_content": "Date,Day of Week,Start Time,End Time,Duration (Hours),Duration (HH:MM),Description,Overtime,Created At\n..."
}
```

## Comparison with CLI

The MCP server provides equivalent functionality to the CLI with these key differences:

### Feature Parity

| Feature | CLI | MCP Server |
|---------|-----|------------|
| Start tracking | ✅ `waqt start` | ✅ `start` tool |
| End tracking | ✅ `waqt end` | ✅ `end` tool |
| View summary | ✅ `waqt summary` | ✅ `summary` tool |
| Export data | ✅ `waqt export` | ✅ `export_entries` tool |
| List entries | ❌ (not in CLI) | ✅ `list_entries` tool |
| Configuration | ✅ (via CLI) | ❌ (excluded per requirements) |

### Behavioral Differences

1. **Output Format:**
   - CLI: Human-readable text output with colors and formatting
   - MCP: Structured JSON responses for programmatic consumption

2. **File Output:**
   - CLI: `export` command writes files to disk
   - MCP: `export_entries` returns CSV content as a string (client can save it)

3. **Additional Features:**
   - MCP: `list_entries` tool provides more flexible entry listing
   - MCP: All responses include structured metadata

4. **Error Handling:**
   - CLI: Exits with error codes and colored error messages
   - MCP: Returns error status in JSON with descriptive messages

## Example Workflows

### Basic Time Tracking

```
1. Start tracking:
   Tool: start
   Input: {"time": "09:00", "description": "Feature development"}

2. End tracking:
   Tool: end
   Input: {"time": "17:30"}

3. View summary:
   Tool: summary
   Input: {"period": "week"}
```

### Data Export

```
1. List entries for review:
   Tool: list_entries
   Input: {"period": "month", "limit": 10}

2. Export to CSV:
   Tool: export_entries
   Input: {"period": "month"}
   
3. Save the csv_content from response to file
```

### Overtime Tracking

```
1. Check weekly summary:
   Tool: summary
   Input: {"period": "week"}
   
2. Review entries with overtime:
   Tool: list_entries
   Input: {"period": "week"}
   (Filter entries where duration_hours > 8)
```

## Integration Testing

The MCP server includes comprehensive integration tests in `tests/test_mcp_server.py`. Run them with:

```bash
pytest tests/test_mcp_server.py -v
```

## Error Handling

All MCP tools return responses with a `status` field:

- `"success"`: Operation completed successfully
- `"error"`: Operation failed, check `message` field for details

Example error response:
```json
{
  "status": "error",
  "message": "Invalid date format '2024-13-45'. Use YYYY-MM-DD."
}
```

## Security Considerations

1. **Database Access:** The MCP server uses the same SQLite database as the CLI and web interface
2. **No Authentication:** The MCP server doesn't implement authentication (relies on MCP client security)
3. **Local Only:** Designed for local use, not exposed over network
4. **Configuration Excluded:** No configuration management via MCP per security requirements

## Troubleshooting

### Server Won't Start

- Ensure waqt is properly installed: `uv pip install -e .`
- Check that database is initialized: `python init_db.py`
- Verify Python version: Requires Python 3.11+

### Database Errors

- The MCP server shares the database with CLI and web interface
- Ensure the database file exists and has proper permissions
- Check `SQLALCHEMY_DATABASE_URI` environment variable if customized

### Tool Execution Fails

- Check tool parameters match the expected format
- Review error messages in the response
- Ensure date/time formats are correct (YYYY-MM-DD, HH:MM)

## Development

### Adding New Tools

To add new tools to the MCP server:

1. Define the tool function with `@mcp.tool()` decorator
2. Add comprehensive docstring (used for tool description)
3. Return structured JSON response with status field
4. Add tests in `tests/test_mcp_server.py`

Example:
```python
@mcp.tool()
def my_new_tool(param: str) -> Dict[str, Any]:
    """Tool description for LLM.
    
    Args:
        param: Parameter description
    
    Returns:
        Dictionary with status and data
    """
    with app.app_context():
        # Implementation
        return {"status": "success", "data": "..."}
```

### Testing

```bash
# Run all MCP tests
pytest tests/test_mcp_server.py -v

# Run specific test
pytest tests/test_mcp_server.py::test_start_basic -v

# Run with coverage
pytest tests/test_mcp_server.py --cov=src.waqt.mcp_server
```

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Waqt CLI Documentation](../README.md#cli-usage-waqt)
- [Waqt Usage Guide](./usage.md)
