#!/usr/bin/env python3
"""
Basic MCP Client Example

Demonstrates how to connect to and interact with MCP servers:
- Connecting to servers via different transports
- Listing and calling tools
- Reading resources
- Getting prompts

Run with: python examples/clients/basic_client.py
"""

import asyncio
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def demonstrate_basic_client():
    """Demonstrate basic MCP client functionality."""
    
    # Server parameters for connecting to our basic server
    server_params = StdioServerParameters(
        command="python",
        args=["examples/servers/basic_server.py"],
    )
    
    print("🔌 Connecting to MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            print("✅ Connected successfully!")
            
            # List available tools
            print("\n🔧 Available Tools:")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # List available resources
            print("\n📚 Available Resources:")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.name}")
            
            # List available prompts
            print("\n💬 Available Prompts:")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            
            # Demonstrate tool calling
            print("\n🧮 Calling tools:")
            
            # Call add_numbers tool
            result = await session.call_tool("add_numbers", {"a": 15, "b": 27})
            print(f"  add_numbers(15, 27) = {result.content[0].text}")
            
            # Call get_current_time tool
            result = await session.call_tool("get_current_time", {})
            print(f"  Current time: {result.content[0].text}")
            
            # Call calculate_area tool
            result = await session.call_tool(
                "calculate_area", 
                {"shape": "circle", "radius": 5}
            )
            print(f"  Circle area (radius=5): {result.content[0].text}")
            
            # Demonstrate resource reading
            print("\n📖 Reading resources:")
            
            # Read server info resource
            resource_content = await session.read_resource("info://server")
            print(f"  Server info: {resource_content.contents[0].text[:100]}...")
            
            # Read capabilities resource
            resource_content = await session.read_resource("config://capabilities")
            print(f"  Capabilities: {resource_content.contents[0].text[:100]}...")
            
            # Read math examples resource
            resource_content = await session.read_resource("examples://math/addition")
            print(f"  Math examples: {resource_content.contents[0].text}")
            
            # Demonstrate prompt usage
            print("\n💭 Getting prompts:")
            
            # Get math helper prompt
            prompt_result = await session.get_prompt(
                "math_helper", 
                {"problem": "Calculate the area of a rectangle with width 8 and height 6"}
            )
            print(f"  Math helper prompt: {prompt_result.messages[0].content.text[:100]}...")
            
            # Get server introduction prompt
            prompt_result = await session.get_prompt("server_introduction", {})
            print(f"  Introduction: {prompt_result.messages[0].content.text[:100]}...")


async def demonstrate_filesystem_client():
    """Demonstrate client interaction with filesystem server."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["examples/servers/filesystem_server.py"],
    )
    
    print("\n" + "="*60)
    print("🗂️  Filesystem Server Demo")
    print("="*60)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to filesystem server!")
            
            # Get current directory
            resource_content = await session.read_resource("fs://cwd")
            current_dir = resource_content.contents[0].text
            print(f"\n📁 Current directory: {current_dir}")
            
            # List directory contents
            result = await session.call_tool("list_directory", {"dir_path": "."})
            print(f"\n📋 Directory contents: {result.content[0].text[:200]}...")
            
            # Get file info for this script
            result = await session.call_tool(
                "get_file_info", 
                {"file_path": "examples/clients/basic_client.py"}
            )
            print(f"\n📄 This file info: {result.content[0].text[:200]}...")
            
            # Search for Python files
            result = await session.call_tool(
                "search_files", 
                {"directory": ".", "pattern": "*.py", "max_results": 5}
            )
            print(f"\n🔍 Python files found: {result.content[0].text[:200]}...")


async def main():
    """Main function to run client demonstrations."""
    try:
        await demonstrate_basic_client()
        await demonstrate_filesystem_client()
        
        print("\n" + "="*60)
        print("🎉 Client demonstrations completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 