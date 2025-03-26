"""
Tests for the proxy tool.

This module contains tests for the proxy tool that forwards requests to remote MCP servers.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from mcp_example.adapters.http.client import MCPClient
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition, FunctionResponse
from mcp_example.tools.proxy import proxy_call, register, list_remote_functions


@pytest.fixture
def mock_client():
    """Fixture to create a mock MCP client."""
    with patch("mcp_example.tools.proxy.MCPClient") as mock_client_class:
        # Create mock instance
        mock_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_instance
        
        # Set up mock function definitions
        mock_function = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Test parameter",
                    }
                },
                "required": ["param1"],
            },
        )
        
        # Set up mock responses
        mock_instance.list_functions.return_value = [mock_function]
        mock_instance.get_function.return_value = mock_function
        mock_instance.call_function.return_value = FunctionResponse(
            result={"value": "test_result"},
            status="success"
        )
        
        yield mock_instance


def test_proxy_call(mock_client):
    """Test proxy_call function."""
    # Call proxy_call function
    result = proxy_call(
        server_url="http://test-server.com",
        function_name="test_function",
        parameters={"param1": "test"},
    )
    
    # Check that the client was called correctly
    mock_client.call_function.assert_called_once_with(
        "test_function", {"param1": "test"}
    )
    
    # Check that the result was returned correctly
    assert result == {"value": "test_result"}


def test_proxy_call_error(mock_client):
    """Test proxy_call function with an error response."""
    # Set up mock error response
    mock_client.call_function.return_value = FunctionResponse(
        result=None,
        error="Test error",
        status="error"
    )
    
    # Call proxy_call function and check for error
    with pytest.raises(ValueError) as exc_info:
        proxy_call(
            server_url="http://test-server.com",
            function_name="test_function",
            parameters={"param1": "test"},
        )
    
    assert "Remote function call failed: Test error" in str(exc_info.value)


def test_list_remote_functions(mock_client):
    """Test list_remote_functions function."""
    # Call list_remote_functions function
    result = list_remote_functions("http://test-server.com")
    
    # Check that the client was called correctly
    mock_client.list_functions.assert_called_once()
    
    # Check that the result was returned correctly
    assert len(result) == 1
    assert result[0].name == "test_function"


def test_register():
    """Test register function."""
    # Mock registry.register to avoid side effects
    with patch("mcp_example.tools.proxy.registry.register") as mock_register:
        # Call register function
        register()
        
        # Check that registry.register was called with correct arguments
        assert mock_register.call_count == 1
        args, _ = mock_register.call_args
        assert len(args) == 2
        assert args[0].name == "proxy"
        assert callable(args[1]) 