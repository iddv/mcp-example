"""
Unit tests for tool result caching functionality.
"""

import time
import unittest
from unittest.mock import patch, MagicMock

from mcp_example.adapters.http.cache import ToolCache
from mcp_example.adapters.http.client import MCPClient, AsyncMCPClient
from mcp_example.core.schema import ToolResponse, FunctionResponse


class TestToolCache(unittest.TestCase):
    """Tests for the ToolCache class."""

    def test_cache_storage_and_retrieval(self):
        """Test basic storage and retrieval of cache entries."""
        cache = ToolCache()
        function_name = "test_function"
        parameters = {"param1": "value1", "param2": 123}
        result = FunctionResponse(result="test_result")

        # Store in cache
        cache.set(function_name, parameters, result)

        # Retrieve from cache
        cached_result = cache.get(function_name, parameters)
        self.assertEqual(cached_result, result)

        # Test with different parameters
        different_params = {"param1": "different", "param2": 456}
        self.assertIsNone(cache.get(function_name, different_params))

    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        cache = ToolCache(ttl=0.1)  # 100ms TTL for quick testing
        function_name = "test_function"
        parameters = {"param": "value"}
        result = FunctionResponse(result="test_result")

        # Store in cache
        cache.set(function_name, parameters, result)
        
        # Should be in cache initially
        self.assertEqual(cache.get(function_name, parameters), result)
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired now
        self.assertIsNone(cache.get(function_name, parameters))

    def test_cache_invalidation(self):
        """Test manual invalidation of cache entries."""
        cache = ToolCache()
        function_name = "test_function"
        parameters = {"param": "value"}
        result = FunctionResponse(result="test_result")

        # Store in cache
        cache.set(function_name, parameters, result)
        
        # Should be in cache
        self.assertEqual(cache.get(function_name, parameters), result)
        
        # Invalidate entry
        self.assertTrue(cache.invalidate(function_name, parameters))
        
        # Should not be in cache anymore
        self.assertIsNone(cache.get(function_name, parameters))
        
        # Invalidating non-existent entry should return False
        self.assertFalse(cache.invalidate(function_name, parameters))

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = ToolCache()
        
        # Add multiple entries
        cache.set("func1", {"param": 1}, FunctionResponse(result="result1"))
        cache.set("func2", {"param": 2}, FunctionResponse(result="result2"))
        
        # Entries should be in cache
        self.assertIsNotNone(cache.get("func1", {"param": 1}))
        self.assertIsNotNone(cache.get("func2", {"param": 2}))
        
        # Clear cache
        cache.clear()
        
        # Cache should be empty
        self.assertIsNone(cache.get("func1", {"param": 1}))
        self.assertIsNone(cache.get("func2", {"param": 2}))

    def test_cache_eviction(self):
        """Test that LRU eviction works when cache is full."""
        cache = ToolCache(max_size=2)  # Only 2 entries max
        
        # Add entries
        cache.set("func1", {"param": 1}, FunctionResponse(result="result1"))
        cache.set("func2", {"param": 2}, FunctionResponse(result="result2"))
        
        # Both should be in cache
        self.assertIsNotNone(cache.get("func1", {"param": 1}))
        self.assertIsNotNone(cache.get("func2", {"param": 2}))
        
        # Access func1 to make func2 the least recently used
        cache.get("func1", {"param": 1})
        
        # Add another entry, should evict func2
        cache.set("func3", {"param": 3}, FunctionResponse(result="result3"))
        
        # func1 and func3 should be in cache, func2 should be evicted
        self.assertIsNotNone(cache.get("func1", {"param": 1}))
        self.assertIsNone(cache.get("func2", {"param": 2}))
        self.assertIsNotNone(cache.get("func3", {"param": 3}))


class TestClientCaching(unittest.TestCase):
    """Tests for the HTTP client caching integration."""

    @patch("httpx.Client")
    def test_sync_client_cache_hit(self, mock_client):
        """Test that the sync client uses cache when available."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "test_result"}
        mock_client_instance = mock_client.return_value
        mock_client_instance._make_request.return_value = mock_response
        
        # Create client with enabled cache
        client = MCPClient("http://example.com", cache_enabled=True)
        
        # We need to patch _make_request directly since it's what we're mocking
        client._make_request = mock_client_instance._make_request
        
        # First call should hit the server
        result1 = client.call_function("test_func", {"param": "value"})
        
        # Second call with same params should use cache
        result2 = client.call_function("test_func", {"param": "value"})
        
        # Both results should be the same
        self.assertEqual(result1.result, result2.result)
        
        # HTTP request should only be made once
        self.assertEqual(mock_client_instance._make_request.call_count, 1)

    @patch("httpx.Client")
    def test_sync_client_cache_disabled(self, mock_client):
        """Test that the sync client bypasses cache when disabled."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "test_result"}
        mock_client_instance = mock_client.return_value
        mock_client_instance._make_request.return_value = mock_response
        
        # Create client with disabled cache
        client = MCPClient("http://example.com", cache_enabled=False)
        
        # We need to patch _make_request directly since it's what we're mocking
        client._make_request = mock_client_instance._make_request
        
        # Make multiple calls
        client.call_function("test_func", {"param": "value"})
        client.call_function("test_func", {"param": "value"})
        
        # HTTP request should be made twice
        self.assertEqual(mock_client_instance._make_request.call_count, 2)

    @patch("httpx.Client")
    def test_sync_client_cache_bypass(self, mock_client):
        """Test that the sync client bypasses cache when requested."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "test_result"}
        mock_client_instance = mock_client.return_value
        mock_client_instance._make_request.return_value = mock_response
        
        # Create client with enabled cache
        client = MCPClient("http://example.com", cache_enabled=True)
        
        # We need to patch _make_request directly since it's what we're mocking
        client._make_request = mock_client_instance._make_request
        
        # First call should hit the server
        client.call_function("test_func", {"param": "value"})
        
        # Second call with use_cache=False should bypass cache
        client.call_function("test_func", {"param": "value"}, use_cache=False)
        
        # HTTP request should be made twice
        self.assertEqual(mock_client_instance._make_request.call_count, 2)

    @patch("httpx.Client")
    def test_sync_client_cache_invalidation(self, mock_client):
        """Test that the sync client properly invalidates cache entries."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "test_result"}
        mock_client_instance = mock_client.return_value
        mock_client_instance._make_request.return_value = mock_response
        
        # Create client with enabled cache
        client = MCPClient("http://example.com", cache_enabled=True)
        
        # We need to patch _make_request directly since it's what we're mocking
        client._make_request = mock_client_instance._make_request
        
        # First call should hit the server
        client.call_function("test_func", {"param": "value"})
        
        # Invalidate the cache entry
        client.invalidate_cache_entry("test_func", {"param": "value"})
        
        # Next call should hit the server again
        client.call_function("test_func", {"param": "value"})
        
        # HTTP request should be made twice
        self.assertEqual(mock_client_instance._make_request.call_count, 2)

    @patch("httpx.Client")
    def test_sync_client_cache_clear(self, mock_client):
        """Test that the sync client properly clears all cache entries."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "test_result"}
        mock_client_instance = mock_client.return_value
        mock_client_instance._make_request.return_value = mock_response
        
        # Create client with enabled cache
        client = MCPClient("http://example.com", cache_enabled=True)
        
        # We need to patch _make_request directly since it's what we're mocking
        client._make_request = mock_client_instance._make_request
        
        # Make calls for different functions
        client.call_function("func1", {"param": 1})
        client.call_function("func2", {"param": 2})
        
        # Clear all cache
        client.clear_cache()
        
        # Next calls should hit the server again
        client.call_function("func1", {"param": 1})
        client.call_function("func2", {"param": 2})
        
        # HTTP request should be made 4 times (2 initial + 2 after clearing)
        self.assertEqual(mock_client_instance._make_request.call_count, 4)


if __name__ == "__main__":
    unittest.main() 