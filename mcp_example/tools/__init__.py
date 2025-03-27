"""
Tools package for Model Context Protocol.

This package contains implementations of various MCP tools.
"""

import logging
from typing import List

from mcp_example.core.registry import registry
from mcp_example.core.schema import Tool

logger = logging.getLogger(__name__)


def register_all_tools() -> None:
    """Register all available tools."""
    # Import and register calculator tool
    from mcp_example.tools import calculator
    calculator.register()

    # Import and register text tool
    from mcp_example.tools import text
    text.register()
    
    # Import and register proxy tool
    from mcp_example.tools import proxy
    proxy.register()
    
    # Import and register weather tool
    from mcp_example.tools import weather
    weather.register()

    logger.info(f"Registered {len(registry.list_tools())} tools")


def get_all_tools() -> List[Tool]:
    """
    Get all registered tools.

    Returns:
        List of all registered tools
    """
    return registry.list_tools()

