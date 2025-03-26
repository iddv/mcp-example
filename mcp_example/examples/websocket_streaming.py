"""
WebSocket Streaming Example

This script demonstrates how to use the WebSocket streaming API to stream
function and tool results from an MCP server.
"""

import asyncio
import json
from typing import Any, Dict

from mcp_example.adapters.http.client import AsyncMCPClient


async def stream_calculator_example(server_url: str) -> None:
    """
    Example of streaming a calculator function.
    
    Args:
        server_url: URL of the MCP server
    """
    print("=== Streaming Calculator Example ===")
    
    async with AsyncMCPClient(server_url) as client:
        print("Sending calculator request...")
        
        async for chunk in client.stream_function(
            "calculator",
            {
                "operation": "add",
                "a": 5,
                "b": 3
            }
        ):
            if chunk.error:
                print(f"Error: {chunk.error}")
                break
                
            print(f"Received chunk {chunk.chunk_id}: {chunk.content}")
            
            if chunk.is_final:
                print("Streaming completed.")


async def stream_text_processing_example(server_url: str) -> None:
    """
    Example of streaming a text processing tool.
    
    Args:
        server_url: URL of the MCP server
    """
    print("\n=== Streaming Text Processing Example ===")
    
    async with AsyncMCPClient(server_url) as client:
        print("Sending text processing request...")
        
        async for chunk in client.stream_tool(
            "text",
            {
                "operation": "to_uppercase",
                "text": "hello world"
            }
        ):
            if chunk.error:
                print(f"Error: {chunk.error}")
                break
                
            print(f"Received chunk {chunk.chunk_id}: {chunk.content}")
            
            if chunk.is_final:
                print("Streaming completed.")


async def main() -> None:
    """Main function to run the examples."""
    server_url = "http://localhost:8000"
    
    await stream_calculator_example(server_url)
    await stream_text_processing_example(server_url)


if __name__ == "__main__":
    asyncio.run(main()) 