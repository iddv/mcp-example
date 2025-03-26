# WebSocket Streaming Implementation

## Overview
This document describes the implementation of WebSocket support for streaming interactions with MCP tools and functions. This feature enables clients to receive incremental updates from long-running operations, enhancing the user experience for tasks that take time to complete. This implementation completes Phase 4.3 of the project plan.

## Implementation Details

### Key Components
1. **StreamingChunk Schema**: Defines the format for streaming partial results.
2. **Async Client**: Implements WebSocket connections for streaming responses.
3. **WebSocket Endpoints**: Server-side support for streaming function and tool results.
4. **Example Script**: Demonstrates how to use the streaming API.

### File Structure
- `mcp_example/core/schema.py`: Added StreamingChunk model for streaming responses.
- `mcp_example/adapters/http/client.py`: Implemented AsyncMCPClient with WebSocket support.
- `mcp_example/server/app.py`: Added WebSocket endpoints for streaming functions and tools.
- `mcp_example/examples/websocket_streaming.py`: Example script demonstrating the streaming API.

## Implementation Approach

### Streaming Response Format
The streaming API uses a chunk-based approach where each chunk contains:
- `chunk_id`: Unique identifier for the chunk
- `call_id`: ID of the function or tool call this chunk belongs to
- `content`: Content of the chunk (could be partial results)
- `is_final`: Flag indicating whether this is the final chunk
- `error`: Error message (if applicable)
- `status`: Status of the chunk (success or error)

### Client Implementation
The AsyncMCPClient class provides asynchronous methods for streaming function and tool results:
- `stream_function()`: Streams results from a function call.
- `stream_tool()`: Streams results from a tool call.

Both methods establish WebSocket connections to the server and yield StreamingChunk objects as they arrive.

### Server Implementation
The server implements two WebSocket endpoints:
- `/api/functions/stream`: For streaming function results.
- `/api/tools/stream`: For streaming tool results.

These endpoints accept the same request formats as their non-streaming counterparts but establish WebSocket connections for delivering results in chunks.

### Current Limitations
The current implementation simulates streaming by sending the entire result as a single chunk. True incremental streaming would require modifying the executor to support chunk-based execution, which is planned for a future update.

## Usage Example

Here's a simplified example of how to use the streaming API:

```python
import asyncio
from mcp_example.adapters.http.client import AsyncMCPClient

async def main():
    async with AsyncMCPClient("http://localhost:8000") as client:
        async for chunk in client.stream_function(
            "calculator",
            {"operation": "add", "a": 5, "b": 3}
        ):
            print(f"Received chunk: {chunk.content}")
            if chunk.is_final:
                print("Streaming completed")

asyncio.run(main())
```

## Design Decisions

### Chunk-Based Approach
We chose a chunk-based approach for streaming to allow for flexible partial results. Each chunk has its own ID and status, making it easy to track progress and handle errors.

### WebSocket Protocol
WebSockets were chosen over HTTP streaming (Server-Sent Events) because:
1. They provide bidirectional communication.
2. They have better browser and client library support.
3. They handle connection management more efficiently.

### Async Implementation
The streaming client is fully asynchronous to support efficient I/O operations, allowing applications to perform other tasks while waiting for chunks.

## Future Enhancements
Potential future enhancements for the WebSocket streaming include:
1. True incremental streaming from function execution.
2. Progress reporting for long-running operations.
3. Stream cancellation support.
4. Client-side stream transformers for post-processing chunks.
5. Authentication token refresh during long-lived streams. 