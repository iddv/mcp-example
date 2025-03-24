"""
Tool executor for Model Context Protocol.

This module provides a tool executor that can execute function calls
against a tool registry.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

# Avoid direct import to prevent circular imports
# from mcp_example.core.registry import ToolRegistry, registry
from mcp_example.core.schema import (
    FunctionCall,
    FunctionDefinition,
    FunctionResponse,
    ToolCall,
    ToolResponse,
)
from mcp_example.core.validation import (
    ValidationException,
    extract_function_call_from_text,
)

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executor for running tool calls."""

    def __init__(self, registry=None):
        """
        Initialize a tool executor.

        Args:
            registry: Optional tool registry to use, defaults to global registry
        """
        self._registry = None
        # Defer registry assignment to avoid circular imports
        if registry is not None:
            self._registry = registry

    @property
    def registry(self):
        """
        Get the registry, importing it if needed.
        """
        if self._registry is None:
            # Import here to avoid circular imports
            from mcp_example.core.registry import registry as global_registry
            self._registry = global_registry
        return self._registry

    def execute_function(
        self, call: Union[Dict[str, Any], FunctionCall]
    ) -> FunctionResponse:
        """
        Execute a function call.

        Args:
            call: Function call to execute

        Returns:
            Function response
        """
        if isinstance(call, dict):
            call = FunctionCall(**call)
        return self.registry.execute(call)

    def execute_tool_call(self, call: Union[Dict[str, Any], ToolCall]) -> ToolResponse:
        """
        Execute a tool call.

        Args:
            call: Tool call to execute

        Returns:
            Tool response
        """
        if isinstance(call, dict):
            call = ToolCall(**call)

        function_response = self.execute_function(call.function)
        return ToolResponse(id=call.id, function=function_response)

    def execute_from_text(self, text: str) -> Optional[FunctionResponse]:
        """
        Extract and execute a function call from text.

        Args:
            text: Text containing a function call

        Returns:
            Function response if a call was found and executed, None otherwise
        """
        func_call_dict = extract_function_call_from_text(text)
        if func_call_dict:
            try:
                func_call = FunctionCall(**func_call_dict)
                return self.execute_function(func_call)
            except ValidationException as e:
                logger.error(f"Invalid function call: {e.message}")
                return FunctionResponse(
                    result=None,
                    error=e.message,
                    status="error",
                )
            except Exception as e:
                logger.exception("Error executing function from text")
                return FunctionResponse(
                    result=None,
                    error=str(e),
                    status="error",
                )
        return None

    def execute_batch(
        self, calls: List[Union[Dict[str, Any], FunctionCall]]
    ) -> List[FunctionResponse]:
        """
        Execute multiple function calls in sequence.

        Args:
            calls: List of function calls to execute

        Returns:
            List of function responses
        """
        responses: List[FunctionResponse] = []
        for call in calls:
            response = self.execute_function(call)
            responses.append(response)
        return responses

    def execute_tool_batch(
        self, calls: List[Union[Dict[str, Any], ToolCall]]
    ) -> List[ToolResponse]:
        """
        Execute multiple tool calls in sequence.

        Args:
            calls: List of tool calls to execute

        Returns:
            List of tool responses
        """
        responses: List[ToolResponse] = []
        for call in calls:
            response = self.execute_tool_call(call)
            responses.append(response)
        return responses

    @staticmethod
    def create_tool_call(
        function_name: str, parameters: Dict[str, Any], call_id: Optional[str] = None
    ) -> ToolCall:
        """
        Create a tool call for a function.

        Args:
            function_name: Name of the function to call
            parameters: Parameters for the function call
            call_id: Optional ID for the tool call, generated if not provided

        Returns:
            Tool call
        """
        function_call = FunctionCall(name=function_name, parameters=parameters)
        return ToolCall(id=call_id or str(uuid.uuid4()), function=function_call)


# Global executor instance - no import needed here
executor = ToolExecutor() 