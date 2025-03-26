"""
Proxy tool for Model Context Protocol.

This module provides a proxy tool for forwarding requests to remote MCP servers.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp_example.adapters.http.client import MCPClient
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition, PropertySchema

logger = logging.getLogger(__name__)

# Cache for remote function definitions
_function_cache: Dict[str, Dict[str, FunctionDefinition]] = {}


def proxy_call(
    server_url: str,
    function_name: str,
    parameters: Dict[str, Any],
    api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> Any:
    """
    Proxy a function call to a remote MCP server.

    Args:
        server_url: URL of the remote MCP server
        function_name: Name of the function to call
        parameters: Parameters for the function call
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds

    Returns:
        Result of the function call

    Raises:
        ValueError: If the function call fails
    """
    logger.info(f"Proxying call to {function_name} on {server_url}")
    
    try:
        with MCPClient(
            base_url=server_url,
            api_key=api_key,
            timeout=timeout
        ) as client:
            # Check if function exists
            if server_url not in _function_cache:
                # Cache functions from this server
                _function_cache[server_url] = {
                    f.name: f for f in client.list_functions()
                }
            
            if function_name not in _function_cache.get(server_url, {}):
                # Fetch function definition if not in cache
                try:
                    func_def = client.get_function(function_name)
                    if server_url in _function_cache:
                        _function_cache[server_url][function_name] = func_def
                except Exception as e:
                    raise ValueError(f"Function '{function_name}' not found on server: {str(e)}")
            
            # Call the function
            response = client.call_function(function_name, parameters)
            
            if response.status == "error":
                raise ValueError(f"Remote function call failed: {response.error}")
            
            return response.result
            
    except Exception as e:
        logger.error(f"Proxy call failed: {str(e)}")
        raise ValueError(f"Proxy call failed: {str(e)}")


def proxy_handler(parameters: Dict[str, Any]) -> Any:
    """
    Handler for the proxy tool that unpacks parameters from a dict.
    
    Args:
        parameters: Dictionary of parameters
        
    Returns:
        Result of the proxied function call
    """
    return proxy_call(
        server_url=parameters["server_url"],
        function_name=parameters["function_name"],
        parameters=parameters["parameters"],
        api_key=parameters.get("api_key"),
        timeout=parameters.get("timeout", 30.0)
    )


# Register the proxy tool
proxy_function = FunctionDefinition(
    name="proxy",
    description="Call a function on a remote MCP server",
    parameters={
        "type": "object",
        "properties": {
            "server_url": {
                "type": "string",
                "description": "URL of the remote MCP server",
            },
            "function_name": {
                "type": "string",
                "description": "Name of the function to call on the remote server",
            },
            "parameters": {
                "type": "object",
                "description": "Parameters to pass to the remote function",
            },
            "api_key": {
                "type": "string",
                "description": "Optional API key for authentication",
            },
            "timeout": {
                "type": "number",
                "description": "Request timeout in seconds",
                "default": 30.0,
            },
        },
        "required": ["server_url", "function_name", "parameters"],
    },
)


def register() -> None:
    """Register the proxy tool in the global registry."""
    registry.register(proxy_function, proxy_handler)


def list_remote_functions(server_url: str, api_key: Optional[str] = None) -> List[FunctionDefinition]:
    """
    List all functions available on a remote MCP server.
    
    Args:
        server_url: URL of the remote MCP server
        api_key: Optional API key for authentication
        
    Returns:
        List of function definitions from the remote server
        
    Raises:
        ValueError: If the server cannot be reached
    """
    try:
        with MCPClient(base_url=server_url, api_key=api_key) as client:
            functions = client.list_functions()
            
            # Update cache
            _function_cache[server_url] = {f.name: f for f in functions}
            
            return functions
    except Exception as e:
        logger.error(f"Failed to list remote functions: {str(e)}")
        raise ValueError(f"Failed to list remote functions: {str(e)}") 