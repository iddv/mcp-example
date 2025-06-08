#!/usr/bin/env python3
"""
🚀 FastMCP 2.0 Server Template

This is your clean starting canvas for building any MCP server!

Copy this file and start building:
cp examples/servers/template_server.py my_awesome_server.py

Features ready to use:
- FastMCP 2.0 enterprise framework
- Multiple transport support (stdio, HTTP, WebSocket)
- Authentication configuration ready
- Session management boilerplate
- Error handling patterns
- Testing setup

For guidance, see:
- examples/servers/minesweeper_server.py (complex example)
- FASTMCP_AI_AGENT_GUIDE.md (complete patterns)
- AI_AGENT_INSTRUCTIONS.md (building instructions)

Run with:
  mcp dev my_awesome_server.py
  python my_awesome_server.py --transport http --port 8000
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel


# ============================================================================
# 🏗️ SERVER SETUP
# ============================================================================

# Create your FastMCP server
mcp = FastMCP("Your Server Name Here")

# Global state management (use proper storage in production)
_server_state = {
    "sessions": {},
    "counters": {"requests": 0, "errors": 0},
    "data": {}
}


# ============================================================================
# 🔐 AUTHENTICATION (Optional - uncomment to enable)
# ============================================================================

# @mcp.set_auth_config
# def get_auth_config():
#     """Configure OAuth 2.0 authentication."""
#     return {
#         "authorization_url": "https://your-auth-server.com/oauth/authorize",
#         "token_url": "https://your-auth-server.com/oauth/token",
#         "client_id": os.getenv("MCP_CLIENT_ID"),
#         "client_secret": os.getenv("MCP_CLIENT_SECRET"),
#         "scopes": ["read", "write", "admin"]
#     }


# ============================================================================
# 🔧 TOOLS - Functions the LLM can execute
# ============================================================================

@mcp.tool
def example_tool(input_text: str, option: str = "default") -> dict:
    """
    Example tool - replace with your functionality!
    
    Args:
        input_text: The text to process
        option: Processing option (default, advanced, etc.)
    
    Returns:
        Dictionary with results
    """
    try:
        _server_state["counters"]["requests"] += 1
        
        # Your logic here!
        result = f"Processed '{input_text}' with option '{option}'"
        
        return {
            "success": True,
            "result": result,
            "processed_at": datetime.now().isoformat(),
            "option_used": option
        }
    except Exception as e:
        _server_state["counters"]["errors"] += 1
        return {"success": False, "error": str(e)}

@mcp.tool
async def async_example_tool(data: Dict[str, Any]) -> dict:
    """
    Example async tool - great for I/O operations!
    
    Args:
        data: Dictionary of data to process
    
    Returns:
        Processed results
    """
    try:
        # Simulate async operation
        await asyncio.sleep(0.1)
        
        # Your async logic here!
        processed_data = {
            "original_keys": list(data.keys()),
            "processed_count": len(data),
            "timestamp": time.time()
        }
        
        return {
            "success": True,
            "processed_data": processed_data,
            "message": "Async processing complete"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool
def manage_session(action: str, session_id: str = None, data: Dict[str, Any] = None) -> dict:
    """
    Session management tool - demonstrates stateful operations.
    
    Args:
        action: Action to perform (create, get, update, delete, list)
        session_id: Session identifier (auto-generated for create)
        data: Session data for create/update operations
    
    Returns:
        Session operation results
    """
    try:
        sessions = _server_state["sessions"]
        
        if action == "create":
            new_session_id = str(uuid.uuid4())[:8]
            sessions[new_session_id] = {
                "id": new_session_id,
                "created_at": datetime.now().isoformat(),
                "data": data or {},
                "last_accessed": datetime.now().isoformat()
            }
            return {"success": True, "action": "created", "session_id": new_session_id}
        
        elif action == "get":
            if session_id not in sessions:
                raise ValueError(f"Session {session_id} not found")
            sessions[session_id]["last_accessed"] = datetime.now().isoformat()
            return {"success": True, "session": sessions[session_id]}
        
        elif action == "update":
            if session_id not in sessions:
                raise ValueError(f"Session {session_id} not found")
            sessions[session_id]["data"].update(data or {})
            sessions[session_id]["last_accessed"] = datetime.now().isoformat()
            return {"success": True, "action": "updated", "session_id": session_id}
        
        elif action == "delete":
            if session_id not in sessions:
                raise ValueError(f"Session {session_id} not found")
            del sessions[session_id]
            return {"success": True, "action": "deleted", "session_id": session_id}
        
        elif action == "list":
            session_list = [
                {
                    "id": sid,
                    "created_at": session["created_at"],
                    "last_accessed": session["last_accessed"]
                }
                for sid, session in sessions.items()
            ]
            return {"success": True, "sessions": session_list, "count": len(session_list)}
        
        else:
            raise ValueError(f"Invalid action: {action}")
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# TODO: Add your custom tools here!
# Examples:
# - Data processing tools
# - API integration tools  
# - File operation tools
# - Game logic tools
# - Calculation tools


# ============================================================================
# 📚 RESOURCES - Data the LLM can access
# ============================================================================

@mcp.resource("info://server")
def get_server_info() -> str:
    """Get information about this server."""
    return f"""
    Server Information
    
    Name: {mcp.name}
    Status: Running
    Created: {datetime.now().isoformat()}
    
    Capabilities:
    ✅ Tools: Custom functionality
    ✅ Resources: Data access
    ✅ Prompts: Workflow guidance
    ✅ Sessions: State management
    ✅ Authentication: Ready (configure in auth section)
    
    Available Tools:
    - example_tool: Basic text processing
    - async_example_tool: Async data processing
    - manage_session: Session state management
    
    Available Resources:
    - info://server: This information
    - stats://current: Live statistics
    - config://features: Feature configuration
    
    Add your custom tools and resources below!
    """

@mcp.resource("stats://current")
def get_current_stats() -> str:
    """Get current server statistics."""
    stats = _server_state["counters"]
    sessions = len(_server_state["sessions"])
    
    return f"""
    Current Server Statistics
    
    Requests Processed: {stats['requests']}
    Errors Encountered: {stats['errors']}
    Active Sessions: {sessions}
    Success Rate: {((stats['requests'] - stats['errors']) / max(stats['requests'], 1)) * 100:.1f}%
    
    Last Updated: {datetime.now().isoformat()}
    Server Uptime: Since startup
    """

@mcp.resource("config://features")
def get_feature_config() -> str:
    """Get server feature configuration."""
    return """
    Feature Configuration
    
    🔧 Available Tools:
    - example_tool: Basic processing with options
    - async_example_tool: Async data operations  
    - manage_session: Session lifecycle management
    
    📚 Available Resources:
    - info://server: Server information and capabilities
    - stats://current: Real-time usage statistics
    - config://features: This feature documentation
    
    💬 Available Prompts:
    - workflow_guide: Step-by-step task guidance
    - troubleshooting_help: Error resolution assistance
    
    🏢 Enterprise Features:
    - Authentication: OAuth 2.0 ready (configure above)
    - Session Management: Built-in state handling
    - Multiple Transports: stdio, HTTP, WebSocket
    - Error Handling: Comprehensive error management
    
    To add new features:
    1. Define new @mcp.tool functions
    2. Add @mcp.resource endpoints  
    3. Create @mcp.prompt templates
    4. Update this configuration
    """

@mcp.resource("data://dynamic/{key}")
def get_dynamic_data(key: str) -> str:
    """
    Example of parameterized resource.
    
    Args:
        key: Data key to retrieve
    """
    # Example dynamic data
    dynamic_content = {
        "timestamp": datetime.now().isoformat(),
        "random_id": str(uuid.uuid4()),
        "server_status": "running",
        "session_count": len(_server_state["sessions"])
    }
    
    if key in dynamic_content:
        return f"Dynamic data for '{key}': {dynamic_content[key]}"
    else:
        available_keys = ", ".join(dynamic_content.keys())
        return f"Available dynamic data keys: {available_keys}"

# TODO: Add your custom resources here!
# Examples:
# - Database query resources
# - File system resources
# - API endpoint resources
# - Configuration resources
# - Real-time data resources


# ============================================================================
# 💬 PROMPTS - Templates for LLM interactions
# ============================================================================

@mcp.prompt
def workflow_guide(task_description: str, complexity: str = "medium") -> str:
    """
    Generate step-by-step workflow guidance.
    
    Args:
        task_description: What the user wants to accomplish
        complexity: Task complexity level (simple, medium, complex)
    """
    return f"""
    Workflow Guide: {task_description}
    Complexity Level: {complexity.title()}
    
    Recommended Approach:
    1. **Analysis Phase**
       - Break down the task requirements
       - Identify available tools and resources
       - Plan the execution strategy
    
    2. **Execution Phase**
       - Start with basic operations using example_tool
       - Use async_example_tool for data processing
       - Manage state with manage_session if needed
    
    3. **Validation Phase**
       - Check results using stats://current
       - Verify data integrity
       - Handle any errors appropriately
    
    Available Tools for This Task:
    - example_tool: For basic text/data processing
    - async_example_tool: For complex data operations
    - manage_session: For maintaining state across operations
    
    Available Resources:
    - info://server: Server capabilities
    - stats://current: Progress monitoring
    - config://features: Feature reference
    
    Next Steps:
    Start by using example_tool to test basic functionality, then build up complexity.
    """

@mcp.prompt
def troubleshooting_help(error_description: str, context: str = "") -> str:
    """
    Generate troubleshooting guidance for errors.
    
    Args:
        error_description: Description of the error or issue
        context: Additional context about when/where the error occurred
    """
    return f"""
    Troubleshooting Guide
    
    Error: {error_description}
    Context: {context}
    
    Diagnostic Steps:
    1. **Check Server Status**
       - Access info://server to verify server capabilities
       - Check stats://current for error patterns
       - Review recent operations
    
    2. **Validate Inputs**
       - Ensure all required parameters are provided
       - Check parameter types and formats
       - Verify data structure requirements
    
    3. **Test Basic Functions**
       - Try example_tool with simple inputs
       - Test session management with manage_session
       - Verify async operations work with async_example_tool
    
    4. **Review Configuration**
       - Check config://features for capability limits
       - Verify authentication settings if applicable
       - Review transport configuration
    
    Common Solutions:
    - Input validation errors: Check parameter types and required fields
    - Session errors: Verify session exists and is active
    - Async errors: Check for proper await usage and timeouts
    - State errors: Review session management and data consistency
    
    If problems persist, check the server logs and consider restarting the server.
    """

# TODO: Add your custom prompts here!
# Examples:
# - Domain-specific workflow guides
# - Code generation templates
# - Analysis frameworks
# - Decision trees
# - Best practice guides


# ============================================================================
# 🚀 SERVER EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    transport = "stdio"  # Default transport
    host = "127.0.0.1"
    port = 8000
    
    # Simple argument parsing
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]
    
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]
    
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    
    # Help option
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"""
🚀 FastMCP 2.0 Server Template

Usage:
  python {sys.argv[0]} [options]

Options:
  --transport TYPE    Transport type: stdio (default), streamable-http
  --host HOST         Host address (default: 127.0.0.1)
  --port PORT         Port number (default: 8000)
  --help, -h          Show this help message

Examples:
  python {sys.argv[0]}                                    # stdio mode
  python {sys.argv[0]} --transport streamable-http       # HTTP server
  python {sys.argv[0]} --transport streamable-http --port 9000  # Custom port

Development:
  mcp dev {sys.argv[0]}                                   # MCP inspector
        """)
        sys.exit(0)
    
    # Start the server
    if transport == "streamable-http":
        print(f"🚀 Starting {mcp.name} on http://{host}:{port}")
        print("🔧 Available endpoints:")
        print(f"   - Tools: Use MCP client to call tools")
        print(f"   - Resources: Access via MCP resource URIs")
        print(f"   - Prompts: Get workflow guidance via MCP prompts")
        print()
        print("💡 Connect your MCP client to start interacting!")
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        print(f"🚀 Starting {mcp.name} in stdio mode...")
        print("💡 Use 'mcp dev' for interactive development!")
        mcp.run()


# ============================================================================
# 📝 DEVELOPMENT NOTES
# ============================================================================

"""
🎯 Next Steps for Your Server:

1. **Customize the Server Name and Description**
   - Update the FastMCP("Your Server Name Here") 
   - Modify the docstring at the top

2. **Add Your Domain Logic**
   - Replace example_tool with your specific functionality
   - Add domain-specific tools for your use case
   - Create resources for your data access needs

3. **Configure Resources**
   - Add URI schemes that make sense for your domain
   - Create dynamic resources with parameters
   - Provide helpful documentation resources

4. **Design Workflow Prompts**
   - Create prompts specific to your domain
   - Add step-by-step guidance for common tasks
   - Include troubleshooting help for your tools

5. **Add Authentication (if needed)**
   - Uncomment the auth_config function
   - Set up your OAuth 2.0 provider
   - Configure appropriate scopes

6. **Testing and Deployment**
   - Test with: mcp dev your_server.py
   - Deploy with: python your_server.py --transport streamable-http
   - Add to Claude Desktop config for integration

7. **Advanced Features**
   - Add WebSocket support for real-time updates
   - Implement database connections
   - Add caching and performance optimizations
   - Create server composition with other MCP servers

📚 Resources:
- FASTMCP_AI_AGENT_GUIDE.md: Complete patterns and examples
- examples/servers/minesweeper_server.py: Complex working example
- AI_AGENT_INSTRUCTIONS.md: Step-by-step building guide

🎮 Happy building!
"""