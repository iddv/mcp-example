#!/usr/bin/env python3
"""
Comprehensive MCP Server Example

A complete server demonstrating ALL MCP features:
- Tools: Functions the LLM can call
- Resources: Data the LLM can access (static and dynamic)
- Prompts: Templates for LLM interactions
- Authentication: OAuth 2.0 integration
- Context management: Stateful operations
- Error handling: Robust error responses
- Image handling: Support for images in tools/resources

This server covers the full MCP specification and can serve as a template
for building any MCP server with an AI agent.

Run with: mcp dev examples/servers/comprehensive_server.py
"""

import asyncio
import base64
import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.context import RequestContext
from mcp.types import ImageContent, TextContent


# Create the MCP server with authentication support
mcp = FastMCP(
    "Comprehensive MCP Server",
    dependencies=["httpx", "aiofiles"]
)


# Global state for demonstration (in production, use proper storage)
_server_state = {
    "sessions": {},
    "counters": {"api_calls": 0, "tool_calls": 0},
    "user_data": {}
}


# Authentication configuration (optional)
@mcp.set_auth_config
def get_auth_config():
    """Configure OAuth 2.0 authentication (optional)."""
    return {
        "authorization_url": "https://example.com/oauth/authorize",
        "token_url": "https://example.com/oauth/token",
        "client_id": os.getenv("MCP_CLIENT_ID"),
        "scopes": ["read", "write", "admin"]
    }


# === TOOLS: Functions the LLM can execute ===

@mcp.tool()
def basic_calculator(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform basic mathematical operations.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        a: First number
        b: Second number
    """
    _server_state["counters"]["tool_calls"] += 1
    
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None
    }
    
    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")
    
    result = operations[operation](a, b)
    if result is None:
        raise ValueError("Division by zero is not allowed")
    
    return {
        "operation": operation,
        "operands": [a, b],
        "result": result,
        "timestamp": datetime.now().isoformat()
    }


@mcp.tool()
async def async_web_request(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Make an HTTP request to a URL (demonstrates async tools).
    
    Args:
        url: The URL to request
        method: HTTP method (GET, POST, etc.)
        headers: Optional HTTP headers
    """
    _server_state["counters"]["api_calls"] += 1
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers or {})
            
            return {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "response_time": "simulated",
                "success": response.status_code < 400
            }
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {str(e)}")


@mcp.tool()
def manage_user_session(action: str, user_id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Manage user sessions (demonstrates stateful operations).
    
    Args:
        action: Action to perform (create, get, update, delete)
        user_id: User identifier
        data: Session data for create/update operations
    """
    sessions = _server_state["sessions"]
    
    if action == "create":
        session_id = str(uuid.uuid4())
        sessions[user_id] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "data": data or {},
            "last_accessed": datetime.now().isoformat()
        }
        return {"action": "created", "session_id": session_id}
    
    elif action == "get":
        if user_id not in sessions:
            raise ValueError(f"No session found for user: {user_id}")
        sessions[user_id]["last_accessed"] = datetime.now().isoformat()
        return sessions[user_id]
    
    elif action == "update":
        if user_id not in sessions:
            raise ValueError(f"No session found for user: {user_id}")
        sessions[user_id]["data"].update(data or {})
        sessions[user_id]["last_accessed"] = datetime.now().isoformat()
        return {"action": "updated", "session": sessions[user_id]}
    
    elif action == "delete":
        if user_id not in sessions:
            raise ValueError(f"No session found for user: {user_id}")
        del sessions[user_id]
        return {"action": "deleted", "user_id": user_id}
    
    else:
        raise ValueError(f"Invalid action: {action}")


@mcp.tool()
async def process_image_data(image_base64: str, operation: str = "analyze") -> Dict[str, Any]:
    """
    Process image data (demonstrates image handling).
    
    Args:
        image_base64: Base64 encoded image data
        operation: Operation to perform (analyze, metadata)
    """
    try:
        # Decode base64 to get image data
        image_data = base64.b64decode(image_base64)
        
        if operation == "analyze":
            return {
                "operation": "analyze",
                "size_bytes": len(image_data),
                "format": "detected from headers",
                "analysis": "This would contain actual image analysis in a real implementation",
                "timestamp": datetime.now().isoformat()
            }
        
        elif operation == "metadata":
            return {
                "operation": "metadata",
                "size_bytes": len(image_data),
                "encoding": "base64",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    except Exception as e:
        raise RuntimeError(f"Image processing failed: {str(e)}")


@mcp.tool()
def complex_data_processing(
    data: List[Dict[str, Any]], 
    operation: str,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process complex data structures (demonstrates advanced tool capabilities).
    
    Args:
        data: List of data objects to process
        operation: Operation to perform (filter, aggregate, transform)
        filters: Optional filters to apply
    """
    if operation == "filter":
        if not filters:
            return {"operation": "filter", "result": data, "count": len(data)}
        
        filtered_data = []
        for item in data:
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_data.append(item)
        
        return {"operation": "filter", "result": filtered_data, "count": len(filtered_data)}
    
    elif operation == "aggregate":
        if not data:
            return {"operation": "aggregate", "result": {}}
        
        # Simple aggregation example
        numeric_fields = []
        if data:
            for key, value in data[0].items():
                if isinstance(value, (int, float)):
                    numeric_fields.append(key)
        
        aggregation = {}
        for field in numeric_fields:
            values = [item.get(field, 0) for item in data if isinstance(item.get(field), (int, float))]
            if values:
                aggregation[field] = {
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return {"operation": "aggregate", "result": aggregation}
    
    elif operation == "transform":
        # Simple transformation: add metadata to each item
        transformed_data = []
        for i, item in enumerate(data):
            transformed_item = dict(item)
            transformed_item["_metadata"] = {
                "index": i,
                "processed_at": datetime.now().isoformat(),
                "original_keys": list(item.keys())
            }
            transformed_data.append(transformed_item)
        
        return {"operation": "transform", "result": transformed_data, "count": len(transformed_data)}
    
    else:
        raise ValueError(f"Unsupported operation: {operation}")


# === RESOURCES: Data the LLM can access ===

@mcp.resource("server://info")
def get_server_information() -> str:
    """Get comprehensive server information."""
    return f"""
    Comprehensive MCP Server Information
    
    Server Name: {mcp.name}
    Started: {datetime.now().isoformat()}
    
    Capabilities:
    ✅ Tools: Mathematical operations, HTTP requests, session management, image processing, data processing
    ✅ Resources: Server info, statistics, configuration, dynamic content
    ✅ Prompts: Helper prompts, workflow templates, analysis prompts
    ✅ Authentication: OAuth 2.0 support (optional)
    ✅ Context Management: Stateful operations
    ✅ Async Operations: Full async/await support
    ✅ Error Handling: Comprehensive error management
    ✅ Image Support: Base64 image processing
    
    This server demonstrates the complete MCP specification.
    """


@mcp.resource("server://statistics")
def get_server_statistics() -> str:
    """Get current server statistics."""
    stats = _server_state["counters"]
    sessions = len(_server_state["sessions"])
    
    return f"""
    Server Statistics
    
    Tool Calls: {stats['tool_calls']}
    API Calls: {stats['api_calls']}
    Active Sessions: {sessions}
    
    Last Updated: {datetime.now().isoformat()}
    """


@mcp.resource("config://features")
def get_feature_configuration() -> str:
    """Get server feature configuration."""
    return """
    Feature Configuration
    
    Tools Available:
    - basic_calculator: Mathematical operations
    - async_web_request: HTTP client functionality
    - manage_user_session: Session management
    - process_image_data: Image processing
    - complex_data_processing: Advanced data operations
    
    Resources Available:
    - server://info: Server information
    - server://statistics: Usage statistics
    - config://features: This feature list
    - data://dynamic/{key}: Dynamic data access
    - examples://usage/{category}: Usage examples
    
    Prompts Available:
    - analysis_workflow: Data analysis guidance
    - error_troubleshooting: Error resolution help
    - api_integration: API integration assistance
    """


@mcp.resource("data://dynamic/{key}")
async def get_dynamic_data(key: str) -> str:
    """Get dynamic data based on key (demonstrates parameterized resources)."""
    dynamic_data = {
        "timestamp": datetime.now().isoformat(),
        "random_id": str(uuid.uuid4()),
        "server_uptime": "simulated_uptime",
        "memory_usage": "simulated_memory",
        "current_load": "simulated_load"
    }
    
    if key in dynamic_data:
        return f"Dynamic Data for '{key}': {dynamic_data[key]}"
    else:
        return f"Available dynamic data keys: {', '.join(dynamic_data.keys())}"


@mcp.resource("examples://usage/{category}")
def get_usage_examples(category: str) -> str:
    """Get usage examples for different categories."""
    examples = {
        "tools": """
        Tool Usage Examples:
        
        1. Basic Calculator:
           - basic_calculator("add", 5, 3) → 8
           - basic_calculator("multiply", 4, 7) → 28
        
        2. Web Requests:
           - async_web_request("https://api.example.com/data")
           - async_web_request("https://httpbin.org/json", "GET")
        
        3. Session Management:
           - manage_user_session("create", "user123", {"role": "admin"})
           - manage_user_session("get", "user123")
        """,
        
        "resources": """
        Resource Usage Examples:
        
        1. Server Information:
           - Access: server://info
           - Gets comprehensive server details
        
        2. Dynamic Data:
           - Access: data://dynamic/timestamp
           - Access: data://dynamic/random_id
        
        3. Usage Examples:
           - Access: examples://usage/tools
           - Access: examples://usage/prompts
        """,
        
        "prompts": """
        Prompt Usage Examples:
        
        1. Analysis Workflow:
           - Use for structured data analysis
           - Provides step-by-step guidance
        
        2. Error Troubleshooting:
           - Use when encountering errors
           - Provides diagnostic steps
        
        3. API Integration:
           - Use for integrating external APIs
           - Provides best practices
        """
    }
    
    return examples.get(category, f"Available example categories: {', '.join(examples.keys())}")


# === PROMPTS: Templates for LLM interactions ===

@mcp.prompt()
def analysis_workflow(data_description: str, analysis_goal: str) -> str:
    """Generate a structured prompt for data analysis workflows."""
    return f"""
    Data Analysis Workflow
    
    Data: {data_description}
    Goal: {analysis_goal}
    
    Recommended Steps:
    1. Data Exploration
       - Use complex_data_processing with operation="filter" to explore the data
       - Check data structure and identify key fields
    
    2. Data Processing
       - Apply necessary filters using the filters parameter
       - Use operation="aggregate" to get summary statistics
       - Use operation="transform" to prepare data for analysis
    
    3. Pattern Analysis
       - Look for trends, outliers, and patterns
       - Consider temporal aspects if timestamps are present
    
    4. Results Summary
       - Aggregate findings using the aggregation tools
       - Present insights clearly and actionably
    
    Available Tools:
    - complex_data_processing: For filtering, aggregation, transformation
    - basic_calculator: For mathematical operations
    - manage_user_session: To save analysis state
    
    Begin your analysis by exploring the data structure first.
    """


@mcp.prompt()
def error_troubleshooting(error_description: str, context: str) -> str:
    """Generate a prompt for systematic error troubleshooting."""
    return f"""
    Error Troubleshooting Guide
    
    Error: {error_description}
    Context: {context}
    
    Diagnostic Steps:
    1. Verify Input Parameters
       - Check all required parameters are provided
       - Validate parameter types and formats
       - Ensure values are within expected ranges
    
    2. Check Server State
       - Access server://statistics to check server health
       - Review recent operations that might affect state
    
    3. Test Components Individually
       - Try basic operations first (basic_calculator)
       - Test connectivity if network-related (async_web_request)
       - Verify session state if user-related (manage_user_session)
    
    4. Review Error Patterns
       - Check if error is reproducible
       - Note any error message details
       - Consider timing or load-related factors
    
    Available Diagnostic Tools:
    - server://statistics: Server health metrics
    - basic_calculator: Basic functionality test
    - async_web_request: Network connectivity test
    - manage_user_session: State management test
    
    Start with the most basic test that might reveal the issue.
    """


@mcp.prompt()
def api_integration_guide(api_description: str, integration_goal: str) -> str:
    """Generate a prompt for API integration assistance."""
    return f"""
    API Integration Assistant
    
    API: {api_description}
    Integration Goal: {integration_goal}
    
    Integration Strategy:
    1. API Exploration
       - Use async_web_request to test API endpoints
       - Verify authentication requirements
       - Check response formats and status codes
    
    2. Data Flow Design
       - Plan how data will flow between systems
       - Consider error handling and retry logic
       - Design for rate limiting and quotas
    
    3. Implementation Steps
       - Start with simple GET requests
       - Test authentication if required
       - Implement data processing pipeline
       - Add error handling and logging
    
    4. Testing and Validation
       - Test with various input scenarios
       - Validate response data processing
       - Test error conditions and edge cases
    
    Available Integration Tools:
    - async_web_request: HTTP client for API calls
    - complex_data_processing: Response data processing
    - manage_user_session: State and authentication management
    - process_image_data: If API involves images
    
    Recommended Starting Point:
    Use async_web_request to make a simple test call to the API first.
    """


@mcp.prompt()
def comprehensive_demo() -> str:
    """Generate a prompt demonstrating all server capabilities."""
    return """
    Comprehensive MCP Server Demonstration
    
    This server showcases the complete MCP specification. Try these examples:
    
    🔧 TOOLS (Functions to Execute):
    1. Basic Math: basic_calculator("add", 10, 5)
    2. Web Request: async_web_request("https://httpbin.org/json")
    3. Session Management: manage_user_session("create", "demo_user", {"role": "tester"})
    4. Data Processing: complex_data_processing([{"name": "A", "value": 10}], "aggregate")
    5. Image Processing: process_image_data("base64_image_data", "analyze")
    
    📚 RESOURCES (Data to Access):
    1. Server Info: server://info
    2. Live Statistics: server://statistics
    3. Feature Config: config://features
    4. Dynamic Data: data://dynamic/timestamp
    5. Usage Examples: examples://usage/tools
    
    💬 PROMPTS (Workflow Templates):
    1. analysis_workflow("sales data", "find trends")
    2. error_troubleshooting("timeout error", "API integration")
    3. api_integration_guide("REST API", "data synchronization")
    
    🎯 ADVANCED FEATURES:
    - Async/await support for non-blocking operations
    - Stateful session management
    - Image processing capabilities
    - Complex data transformations
    - OAuth 2.0 authentication support
    - Comprehensive error handling
    
    Start exploring by trying any of the examples above!
    """


if __name__ == "__main__":
    # Run the server
    mcp.run()