"""
Tests for the basic MCP server example.
"""

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_basic_server_connection():
    """Test that we can connect to the basic server."""
    server_params = StdioServerParameters(
        command="python",
        args=["examples/servers/basic_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test that we can list tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0
            
            # Check for expected tools
            tool_names = [tool.name for tool in tools.tools]
            assert "add_numbers" in tool_names
            assert "get_current_time" in tool_names
            assert "calculate_area" in tool_names


@pytest.mark.asyncio
async def test_basic_server_tools():
    """Test the tools provided by the basic server."""
    server_params = StdioServerParameters(
        command="python",
        args=["examples/servers/basic_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test add_numbers tool
            result = await session.call_tool("add_numbers", {"a": 5, "b": 3})
            assert result.content[0].text == "8.0"
            
            # Test get_current_time tool
            result = await session.call_tool("get_current_time", {})
            assert result.content[0].text  # Should return some timestamp
            
            # Test calculate_area tool
            result = await session.call_tool(
                "calculate_area", 
                {"shape": "rectangle", "width": 4, "height": 5}
            )
            # Result should be a JSON string containing area calculation
            assert "20" in result.content[0].text  # 4 * 5 = 20


@pytest.mark.asyncio
async def test_basic_server_resources():
    """Test the resources provided by the basic server."""
    server_params = StdioServerParameters(
        command="python",
        args=["examples/servers/basic_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test server info resource
            resource = await session.read_resource("info://server")
            assert "Basic MCP Server Example" in resource.contents[0].text
            
            # Test capabilities resource
            resource = await session.read_resource("config://capabilities")
            assert "Server Capabilities" in resource.contents[0].text
            
            # Test math examples resource
            resource = await session.read_resource("examples://math/addition")
            assert "Examples:" in resource.contents[0].text


@pytest.mark.asyncio
async def test_basic_server_prompts():
    """Test the prompts provided by the basic server."""
    server_params = StdioServerParameters(
        command="python",
        args=["examples/servers/basic_server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test math helper prompt
            prompt = await session.get_prompt(
                "math_helper", 
                {"problem": "2 + 2"}
            )
            assert "2 + 2" in prompt.messages[0].content.text
            assert "step by step" in prompt.messages[0].content.text
            
            # Test server introduction prompt
            prompt = await session.get_prompt("server_introduction", {})
            assert "basic MCP server" in prompt.messages[0].content.text.lower() 