# Tool Result Caching Implementation

## Overview
This document describes the implementation of the tool result caching feature for the MCP client. The caching mechanism improves performance by storing the results of tool and function calls and reusing them for identical requests, reducing redundant network calls to remote servers.

## Architecture
The caching system consists of two main components:

1. **ToolCache**: A standalone cache implementation that handles storage, retrieval, and management of cached results.
2. **Client Integration**: Modifications to the HTTP client to utilize the cache for function and tool calls.

## ToolCache Implementation

The `ToolCache` class is implemented in `mcp_example/adapters/http/cache.py` and provides the following features:

- **LRU (Least Recently Used) Eviction**: When the cache reaches its maximum size, the least recently accessed entries are removed first.
- **Time-based Expiration**: Cache entries automatically expire after a configurable time-to-live (TTL).
- **Configurable Size Limit**: The maximum number of entries in the cache can be configured.
- **Enable/Disable Option**: Caching can be enabled or disabled entirely.
- **Invalidation API**: Individual cache entries or the entire cache can be manually invalidated.

### Key Functionality

- **Caching Key Generation**: Cache keys are generated using MD5 hashes of the function name and serialized parameters.
- **Parameter Normalization**: JSON parameters are sorted to ensure consistent key generation regardless of parameter order.
- **Access Time Tracking**: The time of last access is recorded for each entry to support LRU eviction.
- **Automatic Cleanup**: Expired entries are removed when accessed.

## Client Integration

The HTTP client classes (`MCPClient` and `AsyncMCPClient`) were modified to integrate with the cache:

- **Cache Initialization**: Cache is created during client initialization with configurable parameters.
- **Cache Checking**: Before making HTTP requests, the cache is checked for matching entries.
- **Result Caching**: After successful requests, results are stored in the cache.
- **Cache Control**: Functions to clear and invalidate cache entries are provided.
- **Cache Bypass Option**: Individual function calls can bypass the cache when needed.

### Client API Additions

- **Cache Parameters**:
  - `cache_enabled`: Controls whether caching is enabled
  - `cache_max_size`: Maximum number of entries in the cache
  - `cache_ttl`: Default time-to-live for cache entries in seconds

- **New Methods**:
  - `clear_cache()`: Clears all cache entries
  - `invalidate_cache_entry(name, parameters)`: Invalidates a specific cache entry

- **Modified Methods**:
  - Added `use_cache` parameter to `call_function()` and `call_tool()` methods

## Usage Examples

### Basic Usage with Caching Enabled

```python
# Create client with caching enabled (default)
client = MCPClient("https://example.com/api")

# First call will hit the server
result1 = client.call_function("calculator.add", {"a": 1, "b": 2})

# Second call with same parameters will use cached result
result2 = client.call_function("calculator.add", {"a": 1, "b": 2})

# Call with different parameters will hit the server
result3 = client.call_function("calculator.add", {"a": 3, "b": 4})
```

### Bypassing Cache for Specific Calls

```python
# Normal call using cache
result1 = client.call_function("data.fetch", {"id": "123"})

# Force refresh by bypassing cache
result2 = client.call_function("data.fetch", {"id": "123"}, use_cache=False)
```

### Invalidating Cache Entries

```python
# Invalidate specific cache entry
client.invalidate_cache_entry("data.fetch", {"id": "123"})

# Clear entire cache
client.clear_cache()
```

### Disabling Caching

```python
# Create client with caching disabled
client = MCPClient("https://example.com/api", cache_enabled=False)
```

## Testing

The caching functionality is tested in `tests/test_cache.py` with the following test categories:

1. **Basic Cache Tests**: Verifying storage, retrieval, and key generation.
2. **Expiration Tests**: Ensuring entries expire after their TTL.
3. **LRU Eviction Tests**: Validating that the least recently used entries are evicted when the cache is full.
4. **Client Integration Tests**: Testing the HTTP client's interaction with the cache.

## Considerations and Limitations

- **Cache Coherence**: The cache doesn't monitor for changes on the server, so stale data may be returned if the server data changes.
- **Memory Usage**: Large response objects or a high cache size limit can increase memory usage.
- **Non-Deterministic Functions**: Functions with side effects or non-deterministic results should be used with caching disabled or with appropriate TTL values.
- **Parameter Comparison**: Only exact parameter matches are considered cache hits, even if semantically equivalent (e.g., order of array elements might matter).

## Future Enhancements

Potential future improvements to the caching system:

- **Cache Persistence**: Ability to persist the cache to disk between program runs.
- **Cache Prefetching**: Proactively cache results for frequently used functions.
- **Smarter Invalidation**: Invalidate related cache entries when a function is called that might affect them.
- **Custom Key Generation**: Allow custom key generation functions for special cases.
- **Metrics Collection**: Track cache hit/miss rates and other performance metrics. 