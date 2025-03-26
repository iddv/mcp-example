"""
Tests for core MCP functionality.

This module contains basic tests for the core MCP components.
"""

import pytest
from typing import Any, Dict

from mcp_example.core.registry import ToolRegistry
from mcp_example.core.schema import FunctionCall, FunctionDefinition, FunctionResponse
from mcp_example.core.validation import validate_function_definition, ValidationException


def test_tool_registry():
    """Test the ToolRegistry class."""
    # Create registry
    registry = ToolRegistry()
    
    # Create function definition
    function_def = FunctionDefinition(
        name="test_function",
        description="Test function for testing",
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
    
    # Create handler
    def handler(params: Dict[str, Any]) -> str:
        return f"Result: {params.get('param1', '')}"
    
    # Register function
    registry.register(function_def, handler)
    
    # Check that function was registered
    assert len(registry.list_tools()) == 1
    assert registry.get_function_definition("test_function") is not None
    
    # Execute function
    call = FunctionCall(name="test_function", parameters={"param1": "test_value"})
    response = registry.execute(call)
    
    # Check response
    assert response.status == "success"
    assert response.result == "Result: test_value"
    assert response.error is None


def test_function_validation():
    """Test function definition validation."""
    # Valid function definition
    valid_func = FunctionDefinition(
        name="valid_function",
        description="Valid function definition",
        parameters={
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "String parameter",
                },
                "param2": {
                    "type": "number",
                    "description": "Number parameter",
                },
            },
            "required": ["param1"],
        },
    )
    
    # Validate should not raise an exception
    validate_function_definition(valid_func)
    
    # Invalid function definition (missing description)
    invalid_func = FunctionDefinition(
        name="invalid_function",
        description="",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    
    # Validate should raise ValidationException
    with pytest.raises(ValidationException) as exc_info:
        validate_function_definition(invalid_func)
    
    assert "Function description must not be empty" in str(exc_info.value)


def test_function_execution():
    """Test function execution with the registry."""
    # Create registry
    registry = ToolRegistry()
    
    # Create and register a simple calculator function
    calc_func = FunctionDefinition(
        name="add",
        description="Add two numbers",
        parameters={
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number",
                },
                "b": {
                    "type": "number",
                    "description": "Second number",
                },
            },
            "required": ["a", "b"],
        },
    )
    
    def add_handler(params: Dict[str, Any]) -> float:
        return params["a"] + params["b"]
    
    registry.register(calc_func, add_handler)
    
    # Test successful execution
    response = registry.execute(FunctionCall(name="add", parameters={"a": 2, "b": 3}))
    assert response.status == "success"
    assert response.result == 5
    
    # Test execution with invalid parameters
    response = registry.execute(FunctionCall(name="add", parameters={"a": 2}))
    assert response.status == "error"
    assert "required property" in response.error
    
    # Test execution with non-existent function
    response = registry.execute(FunctionCall(name="subtract", parameters={"a": 5, "b": 3}))
    assert response.status == "error"
    assert "Function 'subtract' not found" in response.error 