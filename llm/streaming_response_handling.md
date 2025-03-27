# Streaming Response Handling

## Overview

The streaming response handling component provides a standardized way to process and yield streaming outputs from LLM models, particularly AWS Bedrock's Claude 3.7 model. This implementation allows the Model Context Protocol (MCP) to properly handle continuous data streams rather than waiting for complete responses, enabling real-time interaction and response handling for both content and function calls.

## Implementation Details

### Core Components

1. **StreamingChunk Schema**: Defined in `mcp_example/core/schema.py`, this Pydantic model represents individual chunks in a streaming response with fields for:
   - `chunk_id`: Unique identifier for each chunk
   - `call_id`: ID linking chunks to a specific function/tool call
   - `content`: The actual content payload
   - `is_final`: Boolean indicating if this is the final chunk
   - `error`: Optional error message
   - `status`: Success/error status

2. **BedrockClient Streaming Implementation**: The `invoke_model_with_response_stream` methods in both synchronous and asynchronous client implementations handle the AWS Bedrock API's streaming responses.

3. **Claude Adapter Streaming Implementation**: The `generate_with_streaming` methods in both `ClaudeAdapter` and `AsyncClaudeAdapter` classes convert Bedrock's raw streaming format into the standardized MCP streaming chunks.

### Key Design Decisions

1. **Content Accumulation**: The implementation tracks partial content across chunks to build a complete response, which is particularly important for capturing function calls that might be split across multiple chunks.

2. **Function Call Parsing**: The streaming implementation identifies and extracts function calls from the content, converting them into the standard MCP format.

3. **Error Handling**: Each chunk includes error information and status, allowing immediate error detection rather than waiting for the entire stream to complete.

4. **Async/Sync Support**: Both synchronous and asynchronous implementations are provided to support different usage patterns.

## Example Usage

### Basic Synchronous Streaming

```python
from mcp_example.adapters.aws import ClaudeAdapter, ClaudeMessage, ClaudeRole

# Initialize the adapter
adapter = ClaudeAdapter()

# Create a message
message = ClaudeMessage(
    role=ClaudeRole.USER,
    content="What's the weather like in London?"
)

# Stream the response
for chunk in adapter.generate_with_streaming([message]):
    # Process each chunk as it arrives
    print(chunk.content)
    
    # Check if this is the last chunk
    if chunk.is_final:
        print("Streaming completed")
```

### Asynchronous Streaming with Function Calls

```python
import asyncio
from mcp_example.adapters.aws import AsyncClaudeAdapter, ClaudeMessage, ClaudeRole
from mcp_example.core.schema import FunctionDefinition

# Define a function
weather_function = FunctionDefinition(
    name="get_weather",
    description="Get weather information for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit"
            }
        },
        "required": ["location"]
    }
)

async def main():
    # Initialize the adapter
    adapter = AsyncClaudeAdapter()
    
    # Create a message
    message = ClaudeMessage(
        role=ClaudeRole.USER,
        content="What's the weather like in London?"
    )
    
    # Stream the response
    async for chunk in adapter.generate_with_streaming([message], [weather_function]):
        # Process each chunk as it arrives
        print(chunk.content)
        
        # Check if this is the last chunk
        if chunk.is_final:
            print("Streaming completed")

# Run the async function
asyncio.run(main())
```

## Testing Approach

The streaming implementation is tested using pytest with both unit and integration tests:

1. **Mock Tests**: Using pytest's mocking capabilities to simulate AWS Bedrock's streaming responses
2. **Asynchronous Testing**: Using pytest-asyncio to test asynchronous methods
3. **Edge Case Coverage**: Testing error conditions, empty streams, and partial content scenarios

Test coverage includes:
- Normal streaming scenarios with text-only responses
- Streaming with function calls
- Error handling within streams
- Proper accumulation of content across multiple chunks

## Future Improvements

1. **Backpressure Handling**: Add support for controlling the rate of chunk processing in high-throughput scenarios
2. **Custom Content Filtering**: Allow custom filters to process or transform chunks before yielding them
3. **Timeout Management**: Implement configurable timeouts for streaming operations
4. **Resumable Streams**: Add capability to resume streams after interruptions
5. **Stream Telemetry**: Add built-in metrics tracking for streaming performance
6. **Tool-specific Streaming**: Enhance the implementation to better handle tool-specific streaming formats 