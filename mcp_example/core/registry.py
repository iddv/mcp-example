"""
Tool registry for Model Context Protocol.

This module provides a registry for managing available tools and their function definitions.
"""

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from mcp_example.core.schema import (
    FunctionCall,
    FunctionDefinition,
    FunctionResponse,
    Tool,
)
from mcp_example.core.validation import (
    ValidationException,
    validate_function_call,
    validate_function_definition,
)

logger = logging.getLogger(__name__)

# Type for function handlers
T = TypeVar("T")
FunctionHandler = Callable[[Dict[str, Any]], Any]


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, FunctionHandler] = {}

    def register(
        self, function_def: FunctionDefinition, handler: FunctionHandler
    ) -> None:
        """
        Register a tool with its function definition and handler.

        Args:
            function_def: Function definition for the tool
            handler: Function handler for the tool

        Raises:
            ValidationException: If the function definition is invalid
            ValueError: If a tool with the same name is already registered
        """
        # Validate function definition
        validate_function_definition(function_def)

        name = function_def.name
        if name in self._tools:
            raise ValueError(f"Tool with name '{name}' is already registered")

        # Create tool and register
        tool = Tool(function=function_def)
        self._tools[name] = tool
        self._handlers[name] = handler
        logger.info(f"Registered tool: {name}")

    def register_from_function(
        self, func: Callable[..., T], description: Optional[str] = None
    ) -> None:
        """
        Register a tool from a Python function using introspection.

        Args:
            func: Python function to register as a tool
            description: Optional description for the function

        Raises:
            ValidationException: If the function cannot be converted to a tool
            ValueError: If a tool with the same name is already registered
        """
        # Get function name and signature
        name = func.__name__
        sig = inspect.signature(func)
        doc = func.__doc__ or ""

        # Create function definition
        function_def = self._function_from_signature(
            name, sig, description or doc
        )

        # Create handler that maps from dict to kwargs
        def handler(params: Dict[str, Any]) -> Any:
            return func(**params)

        # Register the tool
        self.register(function_def, handler)

    def unregister(self, name: str) -> None:
        """
        Unregister a tool by name.

        Args:
            name: Name of the tool to unregister
        """
        if name in self._tools:
            del self._tools[name]
            del self._handlers[name]
            logger.info(f"Unregistered tool: {name}")
        else:
            logger.warning(f"Cannot unregister: tool '{name}' not found")

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            name: Name of the tool to get

        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)

    def get_function_definition(self, name: str) -> Optional[FunctionDefinition]:
        """
        Get a function definition by name.

        Args:
            name: Name of the function to get

        Returns:
            The function definition if found, None otherwise
        """
        tool = self.get_tool(name)
        if tool:
            return tool.function
        return None

    def list_tools(self) -> List[Tool]:
        """
        List all registered tools.

        Returns:
            List of all registered tools
        """
        return list(self._tools.values())

    def list_function_definitions(self) -> List[FunctionDefinition]:
        """
        List all registered function definitions.

        Returns:
            List of all registered function definitions
        """
        return [tool.function for tool in self._tools.values()]

    def execute(self, call: FunctionCall) -> FunctionResponse:
        """
        Execute a function call.

        Args:
            call: Function call to execute

        Returns:
            Function response

        Raises:
            ValidationException: If the function call is invalid
            ValueError: If the function is not registered
        """
        name = call.name
        print(f"Executing function: {name}")
        print(f"Call parameters: {call.parameters}")
        print(f"Registered handlers: {list(self._handlers.keys())}")
        function_def = self.get_function_definition(name)

        if not function_def:
            logger.error(f"Function '{name}' not found in registry")
            return FunctionResponse(
                result=None,
                error=f"Function '{name}' not found",
                status="error",
            )

        try:
            # Validate function call against definition
            validate_function_call(call, function_def)

            # Get handler and execute
            handler = self._handlers[name]
            print(f"Handler: {handler}")
            result = handler(call.parameters)

            # Create response
            return FunctionResponse(result=result, status="success")

        except ValidationException as e:
            logger.error(f"Validation error: {e.message}")
            return FunctionResponse(
                result=None,
                error=e.message,
                status="error",
            )
        except Exception as e:
            logger.exception(f"Error executing function '{name}'")
            return FunctionResponse(
                result=None,
                error=str(e),
                status="error",
            )

    def _function_from_signature(
        self, name: str, sig: inspect.Signature, description: str
    ) -> FunctionDefinition:
        """
        Create a function definition from a Python function signature.

        Args:
            name: Name of the function
            sig: Function signature
            description: Function description

        Returns:
            Function definition
        """
        from mcp_example.core.schema import ParameterSchema, PropertySchema

        properties: Dict[str, PropertySchema] = {}
        required: List[str] = []

        for param_name, param in sig.parameters.items():
            # Skip self, cls, and *args, **kwargs
            if param_name in ("self", "cls") or param.kind in (
                param.VAR_POSITIONAL,
                param.VAR_KEYWORD,
            ):
                continue

            # Get parameter type and description from docstring or annotation
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                # Convert Python type to JSON Schema type
                type_mapping = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                param_type = type_mapping.get(param.annotation, "string")

            # Create property schema
            properties[param_name] = PropertySchema(
                type=param_type,
                description=f"Parameter: {param_name}",
            )

            # Add to required list if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        # Create parameter schema
        parameters = ParameterSchema(
            type="object",
            properties=properties,
            required=required if required else None,
        )

        # Create function definition
        return FunctionDefinition(
            name=name,
            description=description,
            parameters=parameters,
        )


# Global registry instance
registry = ToolRegistry() 