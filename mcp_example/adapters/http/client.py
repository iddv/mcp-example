"""
HTTP client for Model Context Protocol.

This module provides a client for calling remote MCP servers via HTTP.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

import httpx
from httpx import HTTPError, Response, TimeoutException
from pydantic import ValidationError

from mcp_example.core.schema import (
    FunctionCall,
    FunctionDefinition,
    FunctionList,
    FunctionResponse,
    ToolCall,
    ToolResponse,
)

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for calling remote MCP servers."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize an MCP client.

        Args:
            base_url: Base URL of the MCP server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Create HTTP client
        self.client = httpx.Client(timeout=timeout)
        
        # Create auth headers if API key is provided
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "MCPClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()

    def list_functions(self) -> List[FunctionDefinition]:
        """
        List all available functions on the server.

        Returns:
            List of function definitions

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        response = self._make_request("GET", "/api/functions")
        func_list = FunctionList(**response.json())
        return func_list.functions

    def get_function(self, name: str) -> FunctionDefinition:
        """
        Get a function definition by name.

        Args:
            name: Name of the function

        Returns:
            Function definition

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        response = self._make_request("GET", f"/api/functions/{name}")
        return FunctionDefinition(**response.json())

    def call_function(
        self, name: str, parameters: Dict[str, Any]
    ) -> FunctionResponse:
        """
        Call a function on the server.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call

        Returns:
            Function response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        data = {
            "name": name,
            "parameters": parameters,
        }
        response = self._make_request("POST", "/api/functions/call", json=data)
        return FunctionResponse(**response.json())

    def call_tool(
        self, name: str, parameters: Dict[str, Any], call_id: Optional[str] = None
    ) -> ToolResponse:
        """
        Call a tool on the server.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call
            call_id: Optional ID for the tool call

        Returns:
            Tool response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        data = {
            "id": call_id,
            "function": {
                "name": name,
                "parameters": parameters,
            },
        }
        response = self._make_request("POST", "/api/tools/call", json=data)
        return ToolResponse(**response.json())

    def execute_from_text(self, text: str) -> FunctionResponse:
        """
        Execute a function call from text.

        Args:
            text: Text containing a function call

        Returns:
            Function response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        data = {"text": text}
        response = self._make_request("POST", "/api/execute", json=data)
        return FunctionResponse(**response.json())

    def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Response:
        """
        Make an HTTP request to the server with retries.

        Args:
            method: HTTP method
            path: Request path
            **kwargs: Additional arguments for the request

        Returns:
            HTTP response

        Raises:
            HTTPError: If the request fails after all retries
        """
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)
        
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                response = self.client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )
                response.raise_for_status()
                return response
            
            except (HTTPError, TimeoutException) as e:
                last_error = e
                retries += 1
                
                if retries <= self.max_retries:
                    logger.warning(
                        f"Request failed, retrying ({retries}/{self.max_retries}): {str(e)}"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {str(e)}")
                    raise
        
        # This should not happen, but just in case
        assert last_error is not None
        raise last_error 