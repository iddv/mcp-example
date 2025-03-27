"""
Basic Operations Example

This script demonstrates basic usage of MCP tools for common operations:
1. Calculator operations (add, subtract, multiply, divide)
2. Text transformations (uppercase, lowercase, title case, format)

It shows both synchronous and asynchronous approaches.
"""

import asyncio
from typing import Any, Dict

from mcp_example.adapters.http.client import MCPClient, AsyncMCPClient
from mcp_example.core.executor import executor
from mcp_example.tools import register_all_tools


def basic_calculator_examples() -> None:
    """
    Demonstrate basic calculator operations using the local executor.
    """
    print("=== Basic Calculator Examples (Synchronous) ===")
    
    # Ensure tools are registered
    register_all_tools()
    
    # Addition
    add_response = executor.execute_function({
        "name": "calculator",
        "parameters": {
            "operation": "add",
            "a": 25,
            "b": 17
        }
    })
    print(f"25 + 17 = {add_response.result}")
    
    # Subtraction
    subtract_response = executor.execute_function({
        "name": "calculator",
        "parameters": {
            "operation": "subtract",
            "a": 100,
            "b": 42
        }
    })
    print(f"100 - 42 = {subtract_response.result}")
    
    # Multiplication
    multiply_response = executor.execute_function({
        "name": "calculator",
        "parameters": {
            "operation": "multiply",
            "a": 6,
            "b": 7
        }
    })
    print(f"6 * 7 = {multiply_response.result}")
    
    # Division
    divide_response = executor.execute_function({
        "name": "calculator",
        "parameters": {
            "operation": "divide",
            "a": 100,
            "b": 5
        }
    })
    print(f"100 / 5 = {divide_response.result}")


def text_transformation_examples() -> None:
    """
    Demonstrate text transformation operations using the local executor.
    """
    print("\n=== Text Transformation Examples (Synchronous) ===")
    
    # Ensure tools are registered
    register_all_tools()
    
    # Uppercase transformation
    uppercase_response = executor.execute_function({
        "name": "text",
        "parameters": {
            "operation": "to_uppercase",
            "text": "hello world"
        }
    })
    print(f"Uppercase: {uppercase_response.result}")
    
    # Lowercase transformation
    lowercase_response = executor.execute_function({
        "name": "text",
        "parameters": {
            "operation": "to_lowercase",
            "text": "HELLO WORLD"
        }
    })
    print(f"Lowercase: {lowercase_response.result}")
    
    # Title case transformation
    titlecase_response = executor.execute_function({
        "name": "text",
        "parameters": {
            "operation": "to_titlecase",
            "text": "hello world example"
        }
    })
    print(f"Title case: {titlecase_response.result}")
    
    # Format text
    format_response = executor.execute_function({
        "name": "text",
        "parameters": {
            "operation": "format",
            "template": "Hello, {}! Today is {}.",
            "values": ["User", "Monday"]
        }
    })
    print(f"Formatted text: {format_response.result}")


async def remote_calculator_examples(server_url: str) -> None:
    """
    Demonstrate calculator operations using remote server.
    
    Args:
        server_url: URL of the MCP server
    """
    print("\n=== Remote Calculator Examples (Asynchronous) ===")
    
    async with AsyncMCPClient(server_url) as client:
        # Addition
        add_response = await client.call_function(
            "calculator",
            {
                "operation": "add",
                "a": 123,
                "b": 456
            }
        )
        print(f"123 + 456 = {add_response.result}")
        
        # Complex calculation
        multiply_response = await client.call_function(
            "calculator",
            {
                "operation": "multiply",
                "a": 9,
                "b": 9
            }
        )
        
        square_result = multiply_response.result
        
        # Chain with another calculation
        power_response = await client.call_function(
            "calculator",
            {
                "operation": "multiply",
                "a": square_result,
                "b": square_result
            }
        )
        
        print(f"(9 × 9) × (9 × 9) = {power_response.result}")


async def remote_text_examples(server_url: str) -> None:
    """
    Demonstrate text operations using remote server.
    
    Args:
        server_url: URL of the MCP server
    """
    print("\n=== Remote Text Examples (Asynchronous) ===")
    
    async with AsyncMCPClient(server_url) as client:
        # Text transformation with caching
        print("First call (not cached):")
        uppercase_response1 = await client.call_function(
            "text",
            {
                "operation": "to_uppercase",
                "text": "hello from the remote server"
            }
        )
        print(f"Uppercase: {uppercase_response1.result}")
        
        print("\nSecond call (should use cache):")
        uppercase_response2 = await client.call_function(
            "text",
            {
                "operation": "to_uppercase",
                "text": "hello from the remote server"
            }
        )
        print(f"Uppercase (cached): {uppercase_response2.result}")
        
        # Text analysis
        analyze_response = await client.call_function(
            "text",
            {
                "operation": "analyze",
                "text": "Hello world! This is a sample text for analysis."
            }
        )
        print("\nText analysis result:")
        print(f"  Character count: {analyze_response.result['character_count']}")
        print(f"  Word count: {analyze_response.result['word_count']}")
        print(f"  Sentence count: {analyze_response.result['sentence_count']}")


def synchronous_client_example() -> None:
    """Demonstrate synchronous client usage for remote calls."""
    print("\n=== Synchronous Remote Client Example ===")
    
    # Create synchronous client
    client = MCPClient("http://localhost:8000")
    
    try:
        # List available functions
        functions = client.list_functions()
        print("Available functions:")
        for func in functions.functions:
            print(f"  - {func.name}: {func.description}")
        
        # Call calculator function
        calc_response = client.call_function(
            "calculator",
            {
                "operation": "add",
                "a": 10,
                "b": 20
            }
        )
        print(f"\nCalculator result: 10 + 20 = {calc_response.result}")
    finally:
        # Close client
        client.close()


async def main() -> None:
    """Main function to run all examples."""
    server_url = "http://localhost:8000"
    
    # Run local synchronous examples
    basic_calculator_examples()
    text_transformation_examples()
    
    # Run remote examples
    await remote_calculator_examples(server_url)
    await remote_text_examples(server_url)
    
    # Run synchronous client example
    synchronous_client_example()


if __name__ == "__main__":
    asyncio.run(main()) 