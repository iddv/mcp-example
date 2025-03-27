"""
Proxy Tool with Error Handling Example

This script demonstrates how to use the proxy tool to call remote functions
with comprehensive error handling for various failure scenarios:
1. Remote server unavailable
2. Invalid function name
3. Invalid parameters
4. Server errors
5. Timeout handling
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from mcp_example.adapters.http.client import MCPClient, AsyncMCPClient
from mcp_example.core.executor import executor
from mcp_example.tools import register_all_tools

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def proxy_with_try_except(
    server_url: str, 
    function_name: str, 
    parameters: Dict[str, Any],
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Call a remote function using proxy tool with try-except error handling.
    
    Args:
        server_url: URL of the remote MCP server
        function_name: Name of the function to call
        parameters: Parameters for the function call
        timeout: Request timeout in seconds
    
    Returns:
        Result dictionary with either function result or error details
    """
    print(f"Calling remote function '{function_name}' via proxy tool")
    
    # Ensure tools are registered
    register_all_tools()
    
    try:
        proxy_response = executor.execute_function({
            "name": "proxy",
            "parameters": {
                "server_url": server_url,
                "function_name": function_name,
                "parameters": parameters,
                "timeout": timeout
            }
        })
        
        return {
            "success": True,
            "result": proxy_response.result,
            "error": None
        }
    except Exception as e:
        logger.error(f"Error calling remote function {function_name}: {str(e)}")
        return {
            "success": False,
            "result": None,
            "error": str(e)
        }


def run_proxy_examples_with_error_handling() -> None:
    """Execute multiple proxy calls with different error scenarios."""
    print("=== Proxy Tool with Error Handling Examples ===")
    
    # Successful call
    result1 = proxy_with_try_except(
        "http://localhost:8000",
        "calculator",
        {
            "operation": "add",
            "a": 100,
            "b": 50
        }
    )
    
    if result1["success"]:
        print(f"Successful calculator call: 100 + 50 = {result1['result']}")
    else:
        print(f"Calculator call failed: {result1['error']}")
        
    # Invalid function name
    result2 = proxy_with_try_except(
        "http://localhost:8000",
        "nonexistent_function",
        {
            "some_param": "value"
        }
    )
    
    if result2["success"]:
        print(f"Unexpected success for nonexistent function: {result2['result']}")
    else:
        print(f"Expected error for nonexistent function: {result2['error']}")
    
    # Invalid parameters
    result3 = proxy_with_try_except(
        "http://localhost:8000",
        "calculator",
        {
            "operation": "add",
            "a": 10
            # Missing required 'b' parameter
        }
    )
    
    if result3["success"]:
        print(f"Unexpected success with invalid parameters: {result3['result']}")
    else:
        print(f"Expected error with invalid parameters: {result3['error']}")
    
    # Server unavailable
    result4 = proxy_with_try_except(
        "http://nonexistent-server:8000",
        "calculator",
        {
            "operation": "add",
            "a": 5,
            "b": 7
        },
        timeout=2.0  # Short timeout to fail faster
    )
    
    if result4["success"]:
        print(f"Unexpected success with unavailable server: {result4['result']}")
    else:
        print(f"Expected error with unavailable server: {result4['error']}")
        
    # Timeout example
    result5 = proxy_with_try_except(
        "http://localhost:8000",
        "calculator",  # Assuming this would normally take longer
        {
            "operation": "multiply",
            "a": 999999,
            "b": 999999
        },
        timeout=0.001  # Extremely short timeout to trigger a timeout error
    )
    
    if result5["success"]:
        print(f"Call completed despite short timeout: {result5['result']}")
    else:
        print(f"Expected timeout error: {result5['error']}")


async def async_proxy_with_fallback(
    primary_server_url: str,
    backup_server_url: str,
    function_name: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call a remote function with automatic failover to backup server.
    
    Args:
        primary_server_url: URL of the primary MCP server
        backup_server_url: URL of the backup MCP server
        function_name: Name of the function to call
        parameters: Parameters for the function call
        
    Returns:
        Result dictionary from either primary or backup server
    """
    print(f"\n=== Failover Example for {function_name} ===")
    print(f"Trying primary server: {primary_server_url}")
    
    try:
        # Try primary server with short timeout
        async with AsyncMCPClient(primary_server_url, timeout=2.0) as client:
            response = await client.call_function(function_name, parameters)
            print("Primary server responded successfully")
            return {
                "success": True,
                "result": response.result,
                "server": "primary",
                "error": None
            }
    except Exception as primary_error:
        # Log the primary server error
        logger.error(f"Primary server error: {str(primary_error)}")
        print(f"Primary server failed: {str(primary_error)}")
        
        try:
            # Fall back to backup server
            print(f"Trying backup server: {backup_server_url}")
            async with AsyncMCPClient(backup_server_url, timeout=5.0) as client:
                response = await client.call_function(function_name, parameters)
                print("Backup server responded successfully")
                return {
                    "success": True,
                    "result": response.result,
                    "server": "backup",
                    "error": None
                }
        except Exception as backup_error:
            # Both servers failed
            logger.error(f"Backup server error: {str(backup_error)}")
            print(f"Backup server also failed: {str(backup_error)}")
            return {
                "success": False,
                "result": None,
                "server": None,
                "error": f"Primary error: {str(primary_error)}; Backup error: {str(backup_error)}"
            }


async def retry_with_backoff(
    server_url: str,
    function_name: str,
    parameters: Dict[str, Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Dict[str, Any]:
    """
    Call a remote function with exponential backoff retry.
    
    Args:
        server_url: URL of the MCP server
        function_name: Name of the function to call
        parameters: Parameters for the function call
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay on each retry
        
    Returns:
        Result dictionary with either function result or error details
    """
    print(f"\n=== Retry with Backoff Example for {function_name} ===")
    
    delay = initial_delay
    last_error = None
    
    for attempt in range(max_retries + 1):  # +1 for the initial attempt
        try:
            print(f"Attempt {attempt + 1}/{max_retries + 1}...")
            
            async with AsyncMCPClient(server_url, timeout=5.0) as client:
                response = await client.call_function(function_name, parameters)
                
                print(f"Succeeded on attempt {attempt + 1}")
                return {
                    "success": True,
                    "result": response.result,
                    "attempts": attempt + 1,
                    "error": None
                }
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_retries:
                print(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                print(f"All {max_retries + 1} attempts failed")
    
    return {
        "success": False,
        "result": None,
        "attempts": max_retries + 1,
        "error": str(last_error)
    }


async def main() -> None:
    """Main function to run all examples."""
    # Run synchronous proxy examples with error handling
    run_proxy_examples_with_error_handling()
    
    # Run async examples
    # For demo purposes, we'll use the same URL for primary and backup,
    # but in a real scenario these would be different servers
    primary_url = "http://localhost:8000"
    backup_url = "http://localhost:8000"  # In reality, this would be different
    
    # Failover example
    failover_result = await async_proxy_with_fallback(
        # Using a non-existent primary to force failover
        primary_server_url="http://nonexistent-primary:8000",
        backup_server_url=backup_url,
        function_name="text",
        parameters={
            "operation": "to_uppercase",
            "text": "failover example"
        }
    )
    
    if failover_result["success"]:
        print(f"Failover result (from {failover_result['server']} server): {failover_result['result']}")
    else:
        print(f"Failover completely failed: {failover_result['error']}")
    
    # Retry with backoff example
    retry_result = await retry_with_backoff(
        server_url="http://localhost:8000",  # This should succeed
        function_name="calculator",
        parameters={
            "operation": "add",
            "a": 10,
            "b": 20
        }
    )
    
    if retry_result["success"]:
        print(f"Retry succeeded after {retry_result['attempts']} attempts: {retry_result['result']}")
    else:
        print(f"Retry failed after {retry_result['attempts']} attempts: {retry_result['error']}")
    
    # Intentional failure example with retry
    print("\n=== Demonstrating all retries failing ===")
    retry_fail_result = await retry_with_backoff(
        server_url="http://nonexistent-server:8000",
        function_name="calculator",
        parameters={
            "operation": "add",
            "a": 10,
            "b": 20
        },
        max_retries=2,  # Fewer retries to speed up the demo
        initial_delay=0.5
    )
    
    if retry_fail_result["success"]:
        print(f"Unexpected success: {retry_fail_result['result']}")
    else:
        print(f"Expected failure after {retry_fail_result['attempts']} attempts: {retry_fail_result['error']}")


if __name__ == "__main__":
    asyncio.run(main()) 