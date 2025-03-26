"""
HTTP client for Model Context Protocol.

This module provides a client for calling remote MCP servers via HTTP.
"""

import json
import logging
import time
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Union, AsyncIterator, Callable

import httpx
from httpx import HTTPError, Response, TimeoutException
import websockets
from websockets.exceptions import WebSocketException
from pydantic import ValidationError

from mcp_example.core.schema import (
    FunctionCall,
    FunctionDefinition,
    FunctionList,
    FunctionResponse,
    ToolCall,
    ToolResponse,
    StreamingChunk,
)
from mcp_example.adapters.http.cache import ToolCache

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
        cache_enabled: bool = True,
        cache_max_size: int = 100,
        cache_ttl: float = 300.0,
    ):
        """
        Initialize an MCP client.

        Args:
            base_url: Base URL of the MCP server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            cache_enabled: Whether to enable result caching
            cache_max_size: Maximum number of entries in the cache
            cache_ttl: Default time to live for cache entries in seconds
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
            
        # Initialize cache
        self.cache = ToolCache(
            max_size=cache_max_size,
            ttl=cache_ttl,
            enabled=cache_enabled,
        )

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
        self, name: str, parameters: Dict[str, Any], use_cache: bool = True
    ) -> FunctionResponse:
        """
        Call a function on the server.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call
            use_cache: Whether to use cached results if available

        Returns:
            Function response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        # Check cache first if enabled
        if use_cache:
            cached_result = self.cache.get(name, parameters)
            if cached_result is not None and isinstance(cached_result, FunctionResponse):
                logger.debug(f"Cache hit for function {name}")
                return cached_result
                
        data = {
            "name": name,
            "parameters": parameters,
        }
        response = self._make_request("POST", "/api/functions/call", json=data)
        result = FunctionResponse(**response.json())
        
        # Cache the result
        if use_cache:
            self.cache.set(name, parameters, result)
            
        return result

    def call_tool(
        self, name: str, parameters: Dict[str, Any], call_id: Optional[str] = None,
        use_cache: bool = True
    ) -> ToolResponse:
        """
        Call a tool on the server.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call
            call_id: Optional ID for the tool call
            use_cache: Whether to use cached results if available

        Returns:
            Tool response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        # Check cache first if enabled
        if use_cache:
            cached_result = self.cache.get(name, parameters)
            if cached_result is not None and isinstance(cached_result, ToolResponse):
                logger.debug(f"Cache hit for tool {name}")
                return cached_result
                
        data = {
            "id": call_id,
            "function": {
                "name": name,
                "parameters": parameters,
            },
        }
        response = self._make_request("POST", "/api/tools/call", json=data)
        result = ToolResponse(**response.json())
        
        # Cache the result
        if use_cache:
            self.cache.set(name, parameters, result)
            
        return result

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

    def clear_cache(self) -> None:
        """Clear the client's result cache."""
        self.cache.clear()
        
    def invalidate_cache_entry(self, name: str, parameters: Dict[str, Any]) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            name: Name of the function
            parameters: Parameters for the function call
            
        Returns:
            True if an entry was invalidated, False otherwise
        """
        return self.cache.invalidate(name, parameters)


class AsyncMCPClient:
    """Asynchronous client for calling remote MCP servers with WebSocket support."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cache_enabled: bool = True,
        cache_max_size: int = 100,
        cache_ttl: float = 300.0,
    ):
        """
        Initialize an async MCP client.

        Args:
            base_url: Base URL of the MCP server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            cache_enabled: Whether to enable result caching
            cache_max_size: Maximum number of entries in the cache
            cache_ttl: Default time to live for cache entries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Create HTTP client
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Create auth headers if API key is provided
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
            
        # Initialize cache
        self.cache = ToolCache(
            max_size=cache_max_size,
            ttl=cache_ttl,
            enabled=cache_enabled,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncMCPClient":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def list_functions(self) -> List[FunctionDefinition]:
        """
        List all available functions on the server.

        Returns:
            List of function definitions

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        response = await self._make_request("GET", "/api/functions")
        func_list = FunctionList(**response.json())
        return func_list.functions

    async def get_function(self, name: str) -> FunctionDefinition:
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
        response = await self._make_request("GET", f"/api/functions/{name}")
        return FunctionDefinition(**response.json())

    async def call_function(
        self, name: str, parameters: Dict[str, Any], use_cache: bool = True
    ) -> FunctionResponse:
        """
        Call a function on the server.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call
            use_cache: Whether to use cached results if available

        Returns:
            Function response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        # Check cache first if enabled
        if use_cache:
            cached_result = self.cache.get(name, parameters)
            if cached_result is not None and isinstance(cached_result, FunctionResponse):
                logger.debug(f"Cache hit for function {name}")
                return cached_result
                
        data = {
            "name": name,
            "parameters": parameters,
        }
        response = await self._make_request("POST", "/api/functions/call", json=data)
        result = FunctionResponse(**response.json())
        
        # Cache the result
        if use_cache:
            self.cache.set(name, parameters, result)
            
        return result

    async def call_tool(
        self, name: str, parameters: Dict[str, Any], call_id: Optional[str] = None,
        use_cache: bool = True
    ) -> ToolResponse:
        """
        Call a tool on the server.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call
            call_id: Optional ID for the tool call
            use_cache: Whether to use cached results if available

        Returns:
            Tool response

        Raises:
            HTTPError: If the request fails
            ValidationError: If the response is invalid
        """
        # Check cache first if enabled
        if use_cache:
            cached_result = self.cache.get(name, parameters)
            if cached_result is not None and isinstance(cached_result, ToolResponse):
                logger.debug(f"Cache hit for tool {name}")
                return cached_result
                
        data = {
            "id": call_id,
            "function": {
                "name": name,
                "parameters": parameters,
            },
        }
        response = await self._make_request("POST", "/api/tools/call", json=data)
        result = ToolResponse(**response.json())
        
        # Cache the result
        if use_cache:
            self.cache.set(name, parameters, result)
            
        return result

    async def stream_function(
        self, name: str, parameters: Dict[str, Any]
    ) -> AsyncIterator[StreamingChunk]:
        """
        Stream a function call from the server using WebSockets.

        Args:
            name: Name of the function to call
            parameters: Parameters for the function call

        Yields:
            Streaming chunks of function response

        Raises:
            WebSocketException: If the WebSocket connection fails
            ValidationError: If the response chunks are invalid
        """
        request_data = {
            "name": name,
            "parameters": parameters,
        }
        
        ws_path = f"/api/functions/stream"
        ws_url = f"{self.ws_url}{ws_path}"
        extra_headers = {}
        
        if self.api_key:
            extra_headers["X-API-Key"] = self.api_key
        
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                async with websockets.connect(
                    ws_url, 
                    extra_headers=extra_headers,
                    open_timeout=self.timeout
                ) as websocket:
                    # Send the request
                    await websocket.send(json.dumps(request_data))
                    
                    # Receive streaming response
                    async for message in websocket:
                        try:
                            chunk_data = json.loads(message)
                            chunk = StreamingChunk(**chunk_data)
                            yield chunk
                            
                            # If this is the final chunk, exit
                            if chunk.is_final:
                                break
                                
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.error(f"Invalid chunk received: {str(e)}")
                            raise
                
                # If we get here, streaming completed successfully
                return
            
            except WebSocketException as e:
                last_error = e
                retries += 1
                
                if retries <= self.max_retries:
                    logger.warning(
                        f"WebSocket connection failed, retrying ({retries}/{self.max_retries}): {str(e)}"
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"WebSocket connection failed after {self.max_retries} retries: {str(e)}")
                    raise
        
        # This should not happen, but just in case
        assert last_error is not None
        raise last_error

    async def stream_tool(
        self, name: str, parameters: Dict[str, Any], call_id: Optional[str] = None
    ) -> AsyncIterator[StreamingChunk]:
        """
        Stream a tool call from the server using WebSockets.

        Args:
            name: Name of the tool to call
            parameters: Parameters for the tool call
            call_id: Optional ID for the tool call

        Yields:
            Streaming chunks of tool response

        Raises:
            WebSocketException: If the WebSocket connection fails
            ValidationError: If the response chunks are invalid
        """
        # Generate ID if not provided
        call_id = call_id or str(uuid.uuid4())
        
        request_data = {
            "id": call_id,
            "function": {
                "name": name,
                "parameters": parameters,
            },
        }
        
        ws_path = f"/api/tools/stream"
        ws_url = f"{self.ws_url}{ws_path}"
        extra_headers = {}
        
        if self.api_key:
            extra_headers["X-API-Key"] = self.api_key
        
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                async with websockets.connect(
                    ws_url, 
                    extra_headers=extra_headers,
                    open_timeout=self.timeout
                ) as websocket:
                    # Send the request
                    await websocket.send(json.dumps(request_data))
                    
                    # Receive streaming response
                    async for message in websocket:
                        try:
                            chunk_data = json.loads(message)
                            chunk = StreamingChunk(**chunk_data)
                            yield chunk
                            
                            # If this is the final chunk, exit
                            if chunk.is_final:
                                break
                                
                        except (json.JSONDecodeError, ValidationError) as e:
                            logger.error(f"Invalid chunk received: {str(e)}")
                            raise
                
                # If we get here, streaming completed successfully
                return
            
            except WebSocketException as e:
                last_error = e
                retries += 1
                
                if retries <= self.max_retries:
                    logger.warning(
                        f"WebSocket connection failed, retrying ({retries}/{self.max_retries}): {str(e)}"
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"WebSocket connection failed after {self.max_retries} retries: {str(e)}")
                    raise
        
        # This should not happen, but just in case
        assert last_error is not None
        raise last_error

    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Response:
        """
        Make an async HTTP request to the server with retries.

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
                response = await self.client.request(
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
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} retries: {str(e)}")
                    raise
        
        # This should not happen, but just in case
        assert last_error is not None
        raise last_error

    def clear_cache(self) -> None:
        """Clear the client's result cache."""
        self.cache.clear()
        
    def invalidate_cache_entry(self, name: str, parameters: Dict[str, Any]) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            name: Name of the function
            parameters: Parameters for the function call
            
        Returns:
            True if an entry was invalidated, False otherwise
        """
        return self.cache.invalidate(name, parameters) 