"""
Cache implementation for MCP tool results.

This module provides a caching mechanism for tool results to improve performance
and reduce redundant calls to remote tools.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Union, Tuple
import hashlib

from mcp_example.core.schema import ToolResponse, FunctionResponse

logger = logging.getLogger(__name__)


class ToolCache:
    """Cache for tool results."""

    def __init__(
        self,
        max_size: int = 100,
        ttl: float = 300.0,  # 5 minutes default TTL
        enabled: bool = True,
    ):
        """
        Initialize a tool cache.

        Args:
            max_size: Maximum number of entries in the cache
            ttl: Default time to live in seconds
            enabled: Whether caching is enabled
        """
        self.max_size = max_size
        self.default_ttl = ttl
        self.enabled = enabled
        self.cache: Dict[str, Tuple[Union[ToolResponse, FunctionResponse], float]] = {}
        self.access_times: Dict[str, float] = {}

    def get(
        self, function_name: str, parameters: Dict[str, Any]
    ) -> Optional[Union[ToolResponse, FunctionResponse]]:
        """
        Get a cached result for a function call.

        Args:
            function_name: Name of the function
            parameters: Parameters for the function call

        Returns:
            Cached result or None if not found or expired
        """
        if not self.enabled:
            return None

        key = self._make_key(function_name, parameters)
        if key not in self.cache:
            return None

        result, expiration = self.cache[key]
        current_time = time.time()

        # Check if the entry has expired
        if current_time > expiration:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return None

        # Update access time
        self.access_times[key] = current_time
        return result

    def set(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        result: Union[ToolResponse, FunctionResponse],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Cache a result for a function call.

        Args:
            function_name: Name of the function
            parameters: Parameters for the function call
            result: Result to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if not self.enabled:
            return

        key = self._make_key(function_name, parameters)
        current_time = time.time()
        expiration = current_time + (ttl if ttl is not None else self.default_ttl)

        # Evict entries if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict()

        self.cache[key] = (result, expiration)
        self.access_times[key] = current_time

    def invalidate(self, function_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Invalidate a cached result.

        Args:
            function_name: Name of the function
            parameters: Parameters for the function call

        Returns:
            True if an entry was invalidated, False otherwise
        """
        key = self._make_key(function_name, parameters)
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()
        self.access_times.clear()

    def _make_key(self, function_name: str, parameters: Dict[str, Any]) -> str:
        """
        Create a cache key from a function name and parameters.

        Args:
            function_name: Name of the function
            parameters: Parameters for the function call

        Returns:
            Cache key
        """
        # Sort parameters for consistent hashing
        sorted_params = json.dumps(parameters, sort_keys=True)
        key_str = f"{function_name}:{sorted_params}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _evict(self) -> None:
        """
        Evict the least recently used cache entry.
        """
        if not self.access_times:
            return

        # Find the least recently accessed key
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        del self.cache[lru_key]
        del self.access_times[lru_key] 