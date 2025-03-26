"""
Validation utilities for Model Context Protocol schemas.

This module provides functions to validate function definitions, function calls,
and function parameters according to their schemas.
"""

import json
from typing import Any, Dict, List, Optional, Union, cast

import jsonschema
from jsonschema import ValidationError
from pydantic import ValidationError as PydanticValidationError

from mcp_example.core.schema import (
    FunctionCall,
    FunctionDefinition,
    FunctionResponse,
    ParameterSchema,
    PropertySchema,
)


class ValidationException(Exception):
    """Exception raised for validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


def property_schema_to_json_schema(schema: PropertySchema) -> Dict[str, Any]:
    """Convert a PropertySchema to a JSON Schema dictionary."""
    result: Dict[str, Any] = {
        "type": schema.type,
        "description": schema.description,
    }

    if schema.enum is not None:
        result["enum"] = schema.enum

    if schema.format is not None:
        result["format"] = schema.format

    if schema.default is not None:
        result["default"] = schema.default

    if schema.type == "array" and schema.items is not None:
        result["items"] = schema.items

    if schema.type == "object" and schema.properties is not None:
        result["properties"] = {
            name: property_schema_to_json_schema(prop)
            for name, prop in schema.properties.items()
        }
        if schema.required:
            result["required"] = schema.required

    return result


def parameter_schema_to_json_schema(schema: ParameterSchema) -> Dict[str, Any]:
    """Convert a ParameterSchema to a JSON Schema dictionary."""
    result: Dict[str, Any] = {
        "type": schema.type,
        "properties": {
            name: property_schema_to_json_schema(prop)
            for name, prop in schema.properties.items()
        },
    }

    if schema.required:
        result["required"] = schema.required

    return result


def function_definition_to_json_schema(definition: FunctionDefinition) -> Dict[str, Any]:
    """Convert a FunctionDefinition to a JSON Schema dictionary."""
    return parameter_schema_to_json_schema(definition.parameters)


def validate_function_definition(definition: Union[Dict[str, Any], FunctionDefinition]) -> None:
    """
    Validate a function definition against the MCP schema.

    Args:
        definition: Function definition to validate

    Raises:
        ValidationException: If the definition is invalid
    """
    try:
        if isinstance(definition, dict):
            func_def = FunctionDefinition(**definition)
        else:
            func_def = definition

        # Validate that name and description are not empty
        if not func_def.name:
            raise ValidationException("Function name must not be empty")
        
        if not func_def.description:
            raise ValidationException("Function description must not be empty")
        
        # Validate parameters schema
        if not func_def.parameters.properties:
            raise ValidationException("Function must have at least one parameter")
            
        # Additional validation can be added here if needed
    except PydanticValidationError as e:
        raise ValidationException(
            f"Invalid function definition: {str(e)}", {"errors": e.errors()}
        )


def validate_function_call(
    call: Union[Dict[str, Any], FunctionCall], definition: FunctionDefinition
) -> None:
    """
    Validate a function call against its definition.

    Args:
        call: Function call to validate
        definition: Function definition to validate against

    Raises:
        ValidationException: If the call is invalid
    """
    try:
        if isinstance(call, dict):
            func_call = FunctionCall(**call)
        else:
            func_call = call

        # Check if function name matches
        if func_call.name != definition.name:
            raise ValidationException(
                f"Function name mismatch: expected '{definition.name}', got '{func_call.name}'"
            )

        # Convert parameters schema to JSON Schema
        json_schema = function_definition_to_json_schema(definition)

        # Validate parameters against schema
        try:
            jsonschema.validate(instance=func_call.parameters, schema=json_schema)
        except ValidationError as e:
            raise ValidationException(
                f"Invalid function parameters: {e.message}",
                {"path": list(e.path), "schema_path": list(e.schema_path)},
            )

    except PydanticValidationError as e:
        raise ValidationException(
            f"Invalid function call: {str(e)}", {"errors": e.errors()}
        )


def validate_function_response(
    response: Union[Dict[str, Any], FunctionResponse]
) -> None:
    """
    Validate a function response.

    Args:
        response: Function response to validate

    Raises:
        ValidationException: If the response is invalid
    """
    try:
        if isinstance(response, dict):
            FunctionResponse(**response)
        # If it's already a FunctionResponse, no need to validate further
    except PydanticValidationError as e:
        raise ValidationException(
            f"Invalid function response: {str(e)}", {"errors": e.errors()}
        )


def extract_function_call_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract a function call from a text string.
    
    This handles various formats that might be produced by LLMs.
    
    Args:
        text: Text potentially containing a function call
        
    Returns:
        Extracted function call as a dictionary, or None if no call found
    """
    # Look for JSON blocks
    start_markers = [
        '```json\n', 
        '{', 
        '```\n{',
        'function_call(', 
        'tool_call('
    ]
    
    for marker in start_markers:
        if marker in text:
            start_idx = text.find(marker)
            if marker == '{' and not (text[start_idx-1].isspace() or start_idx == 0):
                continue
                
            # Extract the json block
            content = text[start_idx:]
            # Find the matching end marker
            if marker == '{':
                depth = 0
                for i, char in enumerate(content):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            content = content[:i+1]
                            break
            elif marker.startswith('```'):
                end_marker = '```'
                end_idx = content.find(end_marker, len(marker))
                if end_idx != -1:
                    content = content[len(marker):end_idx]
            else:  # function_call or tool_call
                end_marker = ')'
                end_idx = content.find(end_marker, len(marker))
                if end_idx != -1:
                    content = content[len(marker):end_idx]
            
            # Try to parse as JSON
            try:
                # Clean up the content
                content = content.strip()
                if content.startswith('`') and content.endswith('`'):
                    content = content[1:-1]
                
                # Parse JSON
                func_call = json.loads(content)
                
                # Check if it's a valid function call
                if isinstance(func_call, dict):
                    if "name" in func_call and "parameters" in func_call:
                        return func_call
                    elif "function" in func_call and isinstance(func_call["function"], dict):
                        # Handle nested function calls like in tool_call
                        return func_call["function"]
            except json.JSONDecodeError:
                continue
    
    return None 