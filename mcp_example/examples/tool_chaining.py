"""
Tool Chaining Example

This script demonstrates how to chain local and remote tools together.
It uses the calculator tool locally, then sends the result to a remote
text processing tool to create a formatted message.
"""

import asyncio
from typing import Any, Dict

from mcp_example.adapters.http.client import AsyncMCPClient
from mcp_example.core.executor import executor
from mcp_example.core.registry import registry
from mcp_example.tools import register_all_tools


def local_calculation(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform a local calculation using the calculator tool.
    
    Args:
        operation: Math operation to perform (add, subtract, multiply, divide)
        a: First operand
        b: Second operand
        
    Returns:
        Result dictionary with calculation result
    """
    print(f"Performing local calculation: {a} {operation} {b}")
    
    # Ensure tools are registered
    register_all_tools()
    
    # Execute local calculator tool
    response = executor.execute_function({
        "name": "calculator",
        "parameters": {
            "operation": operation,
            "a": a,
            "b": b
        }
    })
    
    print(f"Local calculation result: {response.result}")
    return {"result": response.result}


async def remote_text_processing(server_url: str, text: str, operation: str) -> Dict[str, Any]:
    """
    Perform remote text processing.
    
    Args:
        server_url: URL of the remote MCP server
        text: Text to process
        operation: Text operation to perform
        
    Returns:
        Result dictionary with processed text
    """
    print(f"Sending text to remote server for {operation}")
    
    async with AsyncMCPClient(server_url) as client:
        # Call remote text processing tool
        response = await client.call_function(
            "text",
            {
                "operation": operation,
                "text": text
            }
        )
        
        print(f"Remote text processing result: {response.result}")
        return {"result": response.result}


async def chain_tools(server_url: str) -> None:
    """
    Chain local calculator with remote text processing.
    
    Args:
        server_url: URL of the remote MCP server
    """
    print("=== Tool Chaining Example ===")
    
    # Step 1: Perform local calculation
    calc_result = local_calculation("add", 42, 58)
    
    # Step 2: Format the result as a message
    message = f"The answer is {calc_result['result']}"
    
    # Step 3: Send to remote server for text processing
    final_result = await remote_text_processing(server_url, message, "to_uppercase")
    
    print("\nChained Result:")
    print(f"Original calculation: 42 + 58 = {calc_result['result']}")
    print(f"Final formatted message: {final_result['result']}")


async def proxy_tool_chain() -> None:
    """
    Demonstrate chaining tools using the proxy tool.
    This method uses the proxy tool to call a remote function,
    then processes the result locally.
    """
    print("\n=== Proxy Tool Chaining Example ===")
    
    # Ensure tools are registered (including proxy tool)
    register_all_tools()
    
    # Step 1: Use proxy tool to call remote calculator
    print("Calling remote calculator via proxy tool")
    proxy_response = executor.execute_function({
        "name": "proxy",
        "parameters": {
            "server_url": "http://localhost:8000",
            "function_name": "calculator",
            "parameters": {
                "operation": "multiply",
                "a": 6,
                "b": 7
            }
        }
    })
    
    remote_result = proxy_response.result
    print(f"Remote calculation result: {remote_result}")
    
    # Step 2: Use the result in a local text processing operation
    print("Processing result with local text tool")
    text_response = executor.execute_function({
        "name": "text",
        "parameters": {
            "operation": "format",
            "template": "The product of 6 and 7 is {}!",
            "values": [remote_result]
        }
    })
    
    print("\nChained Result:")
    print(f"Remote calculation: 6 * 7 = {remote_result}")
    print(f"Local formatting: {text_response.result}")


async def main() -> None:
    """Main function to run the examples."""
    server_url = "http://localhost:8000"
    
    await chain_tools(server_url)
    await proxy_tool_chain()


if __name__ == "__main__":
    asyncio.run(main()) 