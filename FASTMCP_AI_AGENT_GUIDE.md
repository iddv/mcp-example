# 🚀 FastMCP 2.0 AI Agent Building Guide

The ultimate guide for AI agents to build enterprise-grade MCP servers using FastMCP 2.0 - the fast, Pythonic way to create Model Context Protocol applications.

## 🎯 Why FastMCP 2.0?

FastMCP 2.0 is the enterprise evolution of the MCP protocol, offering:
- **Higher-level APIs** than the official SDK
- **Multiple transport protocols** (stdio, HTTP, WebSocket)
- **Enterprise features** (authentication, server composition, proxy servers)
- **Developer experience** optimized for rapid prototyping and production deployment
- **Advanced testing** capabilities with in-memory clients

## 📦 Installation & Setup

### Quick Start
```bash
# Install FastMCP 2.0
uv pip install fastmcp

# With WebSocket support
uv pip install fastmcp[websockets]

# Development dependencies
uv pip install fastmcp httpx aiofiles pydantic rich typer
```

### Poetry Setup
```toml
[tool.poetry.dependencies]
python = "^3.10"
fastmcp = "^2.7.1"
httpx = "^0.28.1"
aiofiles = "^24.1.0"
pydantic = "^2.11.5"
websockets = "^12.0"
```

## 🏗️ Server Architecture

### Basic Server Template
```python
#!/usr/bin/env python3
"""
Your FastMCP 2.0 Server
"""
from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import asyncio

# Create server
mcp = FastMCP("Your Server Name")

# Your implementation here...

if __name__ == "__main__":
    # Default stdio transport
    mcp.run()
    
    # HTTP transport
    # mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
```

## 🔧 Core Components

### 1. Tools (@mcp.tool) - Functions LLMs Can Execute

```python
@mcp.tool
def simple_tool(param: str, optional_param: int = 10) -> dict:
    """
    Tool description for LLM.
    
    Args:
        param: Required parameter description
        optional_param: Optional parameter with default
    
    Returns:
        Dictionary with results
    """
    try:
        # Your logic here
        result = {"status": "success", "data": param, "count": optional_param}
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
async def async_tool(url: str) -> dict:
    """Async tool for I/O operations."""
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "success": True
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def complex_data_tool(data: List[Dict[str, Any]], operation: str) -> dict:
    """Handle complex data structures."""
    if operation == "analyze":
        return {
            "count": len(data),
            "keys": list(data[0].keys()) if data else [],
            "summary": "Data analysis complete"
        }
    elif operation == "filter":
        # Implement filtering logic
        return {"filtered_data": data, "count": len(data)}
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

### 2. Resources (@mcp.resource) - Data Access Points

```python
@mcp.resource("info://server")
def server_info() -> str:
    """Static server information."""
    return """
    Server Information
    
    This server provides...
    Available features:
    - Feature 1
    - Feature 2
    """

@mcp.resource("data://item/{item_id}")
def dynamic_resource(item_id: str) -> str:
    """Dynamic resource with URL parameters."""
    return f"Data for item: {item_id}"

@mcp.resource("config://settings/{category}")
async def async_resource(category: str) -> str:
    """Async resource for database/file access."""
    # Simulate async data loading
    await asyncio.sleep(0.1)
    return f"Configuration for {category}"

@mcp.resource("stats://live")
def live_stats() -> str:
    """Real-time statistics resource."""
    import time
    return f"""
    Live Statistics
    Current Time: {time.time()}
    Active Connections: {get_connection_count()}
    """
```

### 3. Prompts (@mcp.prompt) - LLM Interaction Templates

```python
@mcp.prompt
def workflow_guide(task_type: str, complexity: str) -> str:
    """Generate workflow guidance for tasks."""
    return f"""
    {task_type.title()} Workflow Guide
    Complexity Level: {complexity}
    
    Recommended Steps:
    1. Analyze the requirements
    2. Plan your approach
    3. Execute systematically
    4. Validate results
    
    Available Tools:
    - simple_tool: For basic operations
    - async_tool: For external requests
    - complex_data_tool: For data processing
    
    Begin by understanding the task requirements clearly.
    """

@mcp.prompt
def error_troubleshooting(error_type: str, context: str) -> str:
    """Generate error troubleshooting guidance."""
    return f"""
    Error Troubleshooting: {error_type}
    Context: {context}
    
    Diagnostic Steps:
    1. Check input parameters
    2. Verify system state using info://server
    3. Test basic functionality
    4. Review error patterns
    
    Recovery Actions:
    - Retry with validated inputs
    - Check resource availability
    - Consider alternative approaches
    """
```

## 🏢 Enterprise Features

### 1. Multiple Transport Support

```python
# Stdio (default) - for Claude Desktop integration
mcp.run()

# HTTP with streaming support
mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)

# Custom transport configuration
mcp.run(
    transport="streamable-http",
    host="0.0.0.0",  # Allow external connections
    port=8080,
    log_level="INFO"
)
```

### 2. Authentication & Security

```python
import os
from typing import Optional

# Optional authentication configuration
@mcp.set_auth_config
def auth_config():
    """Configure OAuth 2.0 authentication."""
    return {
        "authorization_url": "https://your-auth-server.com/oauth/authorize",
        "token_url": "https://your-auth-server.com/oauth/token",
        "client_id": os.getenv("MCP_CLIENT_ID"),
        "client_secret": os.getenv("MCP_CLIENT_SECRET"),
        "scopes": ["read", "write", "admin"]
    }

# Context-aware tools
@mcp.tool
def protected_operation(data: str, context: Optional[dict] = None) -> dict:
    """Tool that can access authentication context."""
    # Access user info from context if available
    user_id = context.get("user_id") if context else "anonymous"
    
    return {
        "result": f"Processed {data} for user {user_id}",
        "success": True
    }
```

### 3. State Management & Sessions

```python
# Global state (use proper storage in production)
_server_state = {
    "sessions": {},
    "counters": {"requests": 0, "errors": 0},
    "cache": {}
}

@mcp.tool
def create_session(user_id: str, session_data: dict) -> dict:
    """Create a new user session."""
    import uuid
    session_id = str(uuid.uuid4())
    
    _server_state["sessions"][session_id] = {
        "user_id": user_id,
        "created_at": time.time(),
        "data": session_data,
        "last_activity": time.time()
    }
    
    return {"session_id": session_id, "status": "created"}

@mcp.tool
def get_session(session_id: str) -> dict:
    """Retrieve session data."""
    if session_id not in _server_state["sessions"]:
        raise ValueError(f"Session {session_id} not found")
    
    session = _server_state["sessions"][session_id]
    session["last_activity"] = time.time()
    
    return {"session": session, "status": "active"}
```

### 4. Real-time Data & WebSocket Support

```python
import asyncio
import json
from typing import Dict, Set

# WebSocket client tracking
_websocket_clients: Set = set()

@mcp.tool
async def broadcast_update(message: str, data: dict) -> dict:
    """Broadcast real-time updates to connected clients."""
    update = {
        "type": "broadcast",
        "message": message,
        "data": data,
        "timestamp": time.time()
    }
    
    # Simulate WebSocket broadcast
    for client in _websocket_clients:
        try:
            await client.send(json.dumps(update))
        except:
            _websocket_clients.discard(client)
    
    return {"broadcasted_to": len(_websocket_clients), "success": True}

@mcp.resource("stream://live-data")
async def live_data_stream() -> str:
    """Streaming data resource."""
    return f"""
    Live Data Stream
    
    Timestamp: {time.time()}
    Active Streams: {len(_websocket_clients)}
    Data: {json.dumps({"random": random.randint(1, 100)})}
    """
```

## 🧪 Testing & Development

### 1. In-Memory Testing

```python
# Test your server without external dependencies
async def test_server():
    from fastmcp.testing import create_test_client
    
    # Create test client
    client = create_test_client(mcp)
    
    # Test tools
    result = await client.call_tool("simple_tool", {"param": "test"})
    assert result["success"] == True
    
    # Test resources
    info = await client.get_resource("info://server")
    assert "Server Information" in info
    
    print("All tests passed! ✅")

# Run tests
if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        asyncio.run(test_server())
    else:
        mcp.run()
```

### 2. Development Mode

```bash
# Development with auto-reload
mcp dev your_server.py

# HTTP development server
python your_server.py --transport http --port 8000

# Test mode
python your_server.py --test
```

## 🎮 Real-World Examples

### 1. Game Server (Like Our Minesweeper)

```python
@mcp.tool
def new_game(difficulty: str = "beginner") -> dict:
    """Start a new game session."""
    game_id = create_game_session(difficulty)
    return {"game_id": game_id, "status": "started"}

@mcp.tool  
def make_move(game_id: str, x: int, y: int) -> dict:
    """Make a move in the game."""
    result = process_game_move(game_id, x, y)
    return {"result": result, "game_state": get_game_state(game_id)}

@mcp.resource("game://state/{game_id}")
def game_state_resource(game_id: str) -> str:
    """Real-time game state."""
    return format_game_display(game_id)
```

### 2. Data Processing Server

```python
@mcp.tool
async def process_dataset(data_url: str, operation: str) -> dict:
    """Process external datasets."""
    async with httpx.AsyncClient() as client:
        response = await client.get(data_url)
        data = response.json()
        
        if operation == "analyze":
            return analyze_data(data)
        elif operation == "transform":
            return transform_data(data)
        else:
            raise ValueError(f"Unknown operation: {operation}")

@mcp.resource("data://processed/{job_id}")
def get_processed_data(job_id: str) -> str:
    """Get processing results."""
    return get_job_results(job_id)
```

### 3. API Integration Server

```python
@mcp.tool
async def api_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make requests to external APIs."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method, 
            endpoint, 
            json=data if data else None
        )
        return {
            "status": response.status_code,
            "data": response.json(),
            "success": response.status_code < 400
        }

@mcp.tool
def transform_api_response(response: dict, template: str) -> dict:
    """Transform API responses using templates."""
    return apply_transformation_template(response, template)
```

## 🚀 Deployment Patterns

### 1. Development Deployment

```python
if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    transport = "stdio"
    port = 8000
    
    if "--http" in sys.argv:
        transport = "streamable-http"
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])
    
    if transport == "streamable-http":
        print(f"🚀 Server starting on http://localhost:{port}")
        mcp.run(transport=transport, host="127.0.0.1", port=port)
    else:
        mcp.run()
```

### 2. Production Deployment

```python
# production_server.py
import os
import logging
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)

# Production server with environment configuration
mcp = FastMCP(
    name="Production Server",
    dependencies=["httpx", "aiofiles", "redis"]  # Production dependencies
)

# Production tools here...

if __name__ == "__main__":
    # Production configuration from environment
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", 8000))
    
    print(f"🚀 Production server starting on {host}:{port}")
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        log_level="INFO"
    )
```

## 🎯 Best Practices for AI Agents

### 1. Always Use Error Handling
```python
@mcp.tool
def robust_tool(param: str) -> dict:
    """Always wrap in try-catch."""
    try:
        result = your_logic(param)
        return {"success": True, "result": result}
    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Operation failed: {str(e)}"}
```

### 2. Comprehensive Documentation
```python
@mcp.tool
def well_documented_tool(
    required_param: str,
    optional_param: int = 10,
    complex_param: Dict[str, Any] = None
) -> dict:
    """
    Detailed description of what this tool does.
    
    Args:
        required_param: What this parameter is for
        optional_param: What this does (default: 10)
        complex_param: Structure: {"key": "value", "count": int}
    
    Returns:
        Dictionary with structure:
        {
            "success": bool,
            "result": any,
            "metadata": {
                "processed_at": str,
                "version": str
            }
        }
    
    Raises:
        ValueError: When input validation fails
        RuntimeError: When processing fails
    """
```

### 3. Resource Naming Conventions
```python
# Good resource naming
@mcp.resource("info://server/status")       # Server information
@mcp.resource("data://users/{user_id}")     # User data access
@mcp.resource("config://app/{section}")     # Configuration
@mcp.resource("stream://events/live")       # Real-time streams
@mcp.resource("cache://results/{key}")      # Cached data
@mcp.resource("api://external/{service}")   # External API proxy
```

### 4. Prompt Best Practices
```python
@mcp.prompt
def comprehensive_prompt(task: str, context: str, constraints: str) -> str:
    """
    Generate comprehensive guidance prompts.
    
    Include:
    - Clear task description
    - Available tools and resources
    - Step-by-step guidance
    - Examples and best practices
    - Error handling advice
    """
    return f"""
    Task: {task}
    Context: {context}
    Constraints: {constraints}
    
    Available Tools:
    - tool1: Description and usage
    - tool2: Description and usage
    
    Available Resources:
    - resource1: What data it provides
    - resource2: What data it provides
    
    Recommended Approach:
    1. Step one with specific tool usage
    2. Step two with resource access
    3. Step three with validation
    
    Example Usage:
    tool1("example_param")
    
    Success Criteria:
    - Criteria 1
    - Criteria 2
    """
```

## 🎪 Complete Server Template

Use this as your starting template for any FastMCP 2.0 server:

```python
#!/usr/bin/env python3
"""
Your FastMCP 2.0 Server Template
"""
import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Server initialization
mcp = FastMCP("Your Server Name")

# State management
_server_state = {"sessions": {}, "counters": {}}

# Tools
@mcp.tool
def example_tool(param: str) -> dict:
    """Example tool implementation."""
    try:
        return {"success": True, "result": f"Processed: {param}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Resources  
@mcp.resource("info://server")
def server_info() -> str:
    """Server information resource."""
    return "Your server information here"

# Prompts
@mcp.prompt
def example_prompt(task: str) -> str:
    """Example prompt for guidance."""
    return f"Guidance for task: {task}"

# Main execution
if __name__ == "__main__":
    # Transport configuration
    import sys
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()
```

---

## 🎯 Summary

FastMCP 2.0 enables AI agents to build sophisticated, enterprise-ready MCP servers with:

✅ **Simple APIs** - Clean, Pythonic decorators
✅ **Multiple Transports** - stdio, HTTP, WebSocket support  
✅ **Enterprise Features** - Auth, sessions, real-time data
✅ **Testing Tools** - In-memory testing capabilities
✅ **Production Ready** - Logging, error handling, deployment patterns

**Start with the template above and build your next MCP server in minutes!** 🚀