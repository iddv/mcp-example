#!/usr/bin/env python3
"""
Basic MCP Server Example

A simple server demonstrating the core MCP features:
- Tools: Functions the LLM can call
- Resources: Data the LLM can access
- Prompts: Templates for LLM interactions

Run with: mcp dev examples/servers/basic_server.py
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP


# Create the MCP server
mcp = FastMCP("Basic Example Server")


# Tools - Functions the LLM can execute
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


@mcp.tool()
def calculate_area(shape: str, **kwargs: float) -> Dict[str, Any]:
    """
    Calculate the area of different shapes.
    
    Args:
        shape: The shape type ("rectangle", "circle", "triangle")
        **kwargs: Shape-specific parameters
            - rectangle: width, height
            - circle: radius
            - triangle: base, height
    """
    shape = shape.lower()
    
    if shape == "rectangle":
        width = kwargs.get("width", 0)
        height = kwargs.get("height", 0)
        area = width * height
        return {"shape": "rectangle", "area": area, "width": width, "height": height}
    
    elif shape == "circle":
        radius = kwargs.get("radius", 0)
        area = 3.14159 * radius * radius
        return {"shape": "circle", "area": area, "radius": radius}
    
    elif shape == "triangle":
        base = kwargs.get("base", 0)
        height = kwargs.get("height", 0)
        area = 0.5 * base * height
        return {"shape": "triangle", "area": area, "base": base, "height": height}
    
    else:
        raise ValueError(f"Unsupported shape: {shape}")


# Resources - Data the LLM can access
@mcp.resource("info://server")
def get_server_info() -> str:
    """Get information about this MCP server."""
    return """
    Basic MCP Server Example
    
    This server demonstrates the core MCP features:
    - Tools for mathematical calculations
    - Resources for server information
    - Prompts for guided interactions
    
    Available tools:
    - add_numbers: Add two numbers
    - get_current_time: Get current timestamp
    - calculate_area: Calculate area of shapes
    """


@mcp.resource("config://capabilities")
def get_capabilities() -> str:
    """Get the server's capabilities."""
    return """
    Server Capabilities:
    - Mathematical operations
    - Time utilities
    - Geometric calculations
    - Information retrieval
    """


@mcp.resource("examples://math/{operation}")
def get_math_examples(operation: str) -> str:
    """Get examples for mathematical operations."""
    examples = {
        "addition": "Examples: 5 + 3 = 8, 10.5 + 2.3 = 12.8",
        "area": "Examples: rectangle(width=5, height=3) = 15, circle(radius=2) = 12.57",
        "time": "Example: Current time in ISO format"
    }
    
    return examples.get(operation, f"No examples available for: {operation}")


# Prompts - Templates for LLM interactions
@mcp.prompt()
def math_helper(problem: str) -> str:
    """Help solve a mathematical problem step by step."""
    return f"""
    Please help solve this mathematical problem step by step:
    
    Problem: {problem}
    
    Please:
    1. Identify what type of calculation is needed
    2. Use the appropriate tools available
    3. Show your work clearly
    4. Provide the final answer
    """


@mcp.prompt()
def server_introduction() -> str:
    """Introduce the server's capabilities."""
    return """
    Hello! I'm a basic MCP server that can help you with:
    
    🔢 Mathematical calculations (addition, area calculations)
    ⏰ Time utilities (current date/time)
    📊 Information about my capabilities
    
    Try asking me to:
    - Add some numbers together
    - Calculate the area of a shape
    - Tell you the current time
    - Show you examples of what I can do
    
    What would you like to explore?
    """


if __name__ == "__main__":
    # Run the server
    mcp.run() 