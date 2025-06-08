# AI Agent Instructions for Building MCP Servers

This document provides comprehensive instructions for AI agents to build Model Context Protocol (MCP) servers using the official Python SDK.

## Setup and Dependencies

### 1. Install Dependencies
```bash
# Using poetry (recommended)
poetry add "mcp[cli]" httpx aiofiles pydantic

# Using pip
pip install "mcp[cli]" httpx aiofiles pydantic
```

### 2. Basic Imports
```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.context import RequestContext
from mcp.types import ImageContent, TextContent
import asyncio
from typing import Any, Dict, List, Optional, Union
```

## Complete MCP Server Template

### 1. Server Initialization
```python
#!/usr/bin/env python3
"""
[Your Server Description]
"""

from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("Your Server Name")

# Optional: Add dependencies
mcp = FastMCP(
    "Your Server Name",
    dependencies=["httpx", "aiofiles", "other-packages"]
)
```

### 2. Authentication (Optional)
```python
@mcp.set_auth_config
def get_auth_config():
    """Configure OAuth 2.0 authentication."""
    return {
        "authorization_url": "https://example.com/oauth/authorize",
        "token_url": "https://example.com/oauth/token",
        "client_id": os.getenv("CLIENT_ID"),
        "scopes": ["read", "write"]
    }
```

## Core MCP Components

### 1. TOOLS (@mcp.tool())
Functions the LLM can execute. Always include comprehensive docstrings and error handling.

```python
@mcp.tool()
def sync_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Brief description of what this tool does.
    
    Args:
        param1: Description of parameter
        param2: Description with default value
    
    Returns:
        Dictionary with results
    """
    try:
        # Your implementation here
        result = {"status": "success", "data": param1, "count": param2}
        return result
    except Exception as e:
        raise RuntimeError(f"Tool failed: {str(e)}")

@mcp.tool()
async def async_function(url: str) -> Dict[str, Any]:
    """
    Async tool example for I/O operations.
    
    Args:
        url: URL to process
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return {
                "status_code": response.status_code,
                "content_length": len(response.content)
            }
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {str(e)}")
```

### 2. RESOURCES (@mcp.resource())
Data the LLM can access via URI patterns.

```python
@mcp.resource("info://server")
def get_server_info() -> str:
    """Static resource example."""
    return "Server information content here"

@mcp.resource("data://item/{item_id}")
def get_item_data(item_id: str) -> str:
    """Dynamic resource with parameters."""
    return f"Data for item: {item_id}"

@mcp.resource("config://settings/{category}")
async def get_async_config(category: str) -> str:
    """Async resource example."""
    # Async file reading or database access
    return f"Configuration for {category}"
```

### 3. PROMPTS (@mcp.prompt())
Templates for LLM interactions.

```python
@mcp.prompt()
def analysis_prompt(data_type: str, goal: str) -> str:
    """
    Generate analysis workflow prompt.
    
    Args:
        data_type: Type of data to analyze
        goal: Analysis objective
    """
    return f"""
    Data Analysis Workflow for {data_type}
    
    Objective: {goal}
    
    Steps:
    1. Load and explore the data
    2. Clean and validate data quality
    3. Perform analysis based on the goal
    4. Generate insights and recommendations
    
    Available tools:
    - [List relevant tools here]
    
    Begin by exploring the data structure.
    """

@mcp.prompt()
def error_help(error_msg: str) -> str:
    """Help troubleshoot errors."""
    return f"""
    Error Troubleshooting: {error_msg}
    
    Diagnostic steps:
    1. Check input parameters
    2. Verify system state
    3. Test basic functionality
    4. Review error patterns
    """
```

## Advanced Features

### 1. Image Handling
```python
@mcp.tool()
async def process_image(image_base64: str, operation: str) -> Dict[str, Any]:
    """
    Process base64 encoded images.
    
    Args:
        image_base64: Base64 encoded image data
        operation: Processing operation to perform
    """
    import base64
    try:
        image_data = base64.b64decode(image_base64)
        return {
            "operation": operation,
            "size_bytes": len(image_data),
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise RuntimeError(f"Image processing failed: {str(e)}")
```

### 2. State Management
```python
# Global state (use proper storage in production)
_server_state = {"sessions": {}, "counters": {}}

@mcp.tool()
def manage_state(action: str, key: str, value: Any = None) -> Dict[str, Any]:
    """Manage server state."""
    if action == "set":
        _server_state[key] = value
        return {"action": "set", "key": key}
    elif action == "get":
        return {"action": "get", "key": key, "value": _server_state.get(key)}
    else:
        raise ValueError(f"Invalid action: {action}")
```

### 3. Context Management
```python
@mcp.tool()
async def context_aware_function(message: str, context: Context) -> str:
    """Use request context for advanced operations."""
    # Access request metadata, user info, etc.
    return f"Processed: {message} with context"
```

## Error Handling Best Practices

### 1. Always Use Try-Catch
```python
@mcp.tool()
def safe_operation(data: Any) -> Dict[str, Any]:
    """Always wrap operations in try-catch."""
    try:
        # Your logic here
        result = process_data(data)
        return {"success": True, "result": result}
    except ValueError as e:
        raise ValueError(f"Invalid input: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Operation failed: {str(e)}")
```

### 2. Validate Inputs
```python
@mcp.tool()
def validated_function(email: str, age: int) -> Dict[str, Any]:
    """Validate all inputs."""
    if not email or "@" not in email:
        raise ValueError("Invalid email address")
    if age < 0 or age > 150:
        raise ValueError("Age must be between 0 and 150")
    
    return {"email": email, "age": age, "valid": True}
```

## Complete Server Example Structure

```python
#!/usr/bin/env python3
"""
[Server Name and Description]
"""

# Imports
from mcp.server.fastmcp import FastMCP
import asyncio
from typing import Any, Dict, List, Optional

# Server initialization
mcp = FastMCP("Server Name")

# Optional authentication
@mcp.set_auth_config
def get_auth_config():
    # Auth configuration

# Tools
@mcp.tool()
def tool_function():
    # Tool implementation

@mcp.tool()
async def async_tool_function():
    # Async tool implementation

# Resources
@mcp.resource("scheme://path")
def resource_function():
    # Resource implementation

@mcp.resource("scheme://dynamic/{param}")
async def dynamic_resource_function(param: str):
    # Dynamic resource implementation

# Prompts
@mcp.prompt()
def prompt_function(context: str):
    # Prompt implementation

# Main execution
if __name__ == "__main__":
    mcp.run()
```

## Testing Your Server

### 1. Development Mode
```bash
# Test with MCP inspector
mcp dev your_server.py

# Run server directly
python your_server.py
```

### 2. Install for Claude Desktop
```bash
mcp install your_server.py
```

### 3. Client Testing
```python
# Create a test client
from mcp.client import Client

async def test_server():
    async with Client("your_server.py") as client:
        tools = await client.list_tools()
        result = await client.call_tool("your_tool", {"param": "value"})
        print(result)
```

## URI Schemes for Resources

Use descriptive URI schemes:
- `info://` - Server information and metadata
- `config://` - Configuration and settings
- `data://` - Data access and retrieval
- `api://` - External API integrations
- `fs://` - File system resources
- `db://` - Database resources
- `cache://` - Cached data
- `temp://` - Temporary resources

## Security Best Practices

1. **Input Validation**: Always validate and sanitize inputs
2. **Path Safety**: Use `Path.resolve()` for file operations
3. **Error Messages**: Don't expose sensitive information in errors
4. **Rate Limiting**: Implement rate limiting for expensive operations
5. **Authentication**: Use proper authentication for sensitive operations
6. **Logging**: Log important operations without exposing secrets

## Common Patterns

### 1. CRUD Operations
```python
@mcp.tool()
def create_item(name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Create implementation

@mcp.tool()
def read_item(item_id: str) -> Dict[str, Any]:
    # Read implementation

@mcp.tool()
def update_item(item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Update implementation

@mcp.tool()
def delete_item(item_id: str) -> Dict[str, Any]:
    # Delete implementation
```

### 2. File Operations
```python
@mcp.tool()
async def read_file(file_path: str) -> str:
    import aiofiles
    from pathlib import Path
    
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    async with aiofiles.open(path, 'r') as f:
        return await f.read()
```

### 3. API Integrations
```python
@mcp.tool()
async def api_request(endpoint: str, method: str = "GET") -> Dict[str, Any]:
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.request(method, endpoint)
        return {
            "status": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }
```

## When to Use Each Component

- **Tools**: Use for actions, computations, API calls, file operations
- **Resources**: Use for data access, configuration, documentation
- **Prompts**: Use for workflow guidance, templates, help systems

Remember: Always include comprehensive docstrings, proper error handling, and input validation in every function.