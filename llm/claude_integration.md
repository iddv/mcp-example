# Claude 3.7 Integration

## Overview
This component provides adapters for using Claude 3.7 model via AWS Bedrock with the Model Context Protocol. It enables applications to leverage Claude's advanced capabilities, including tool calling (function invocation), while maintaining compatibility with the MCP standard.

## Implementation Details

### Key Components
1. **ClaudeAdapter**: Synchronous adapter for making Claude API calls
2. **AsyncClaudeAdapter**: Asynchronous adapter for making Claude API calls
3. **Message Formatting**: Utilities for translating between MCP and Claude message formats
4. **Tool/Function Integration**: Support for converting MCP functions to Claude tools format
5. **Streaming Support**: Both synchronous and asynchronous streaming capabilities

### Key Design Decisions
- Used Pydantic models for configuration and message validation
- Created both synchronous and asynchronous implementations for flexibility
- Leveraged the existing Bedrock client for AWS API communication
- Implemented streaming with proper mapping to MCP StreamingChunk format
- Added comprehensive error handling and validation

### Claude-Specific Features
- Support for various Claude parameters like temperature, top_p, top_k
- Ability to set tool_choice to control function calling behavior
- Support for both string and structured content in messages

## Example Usage

### Basic Usage
```python
from mcp_example.adapters.aws.claude import ClaudeAdapter, ClaudeMessage, ClaudeRole

# Create adapter
adapter = ClaudeAdapter()

# Create messages
messages = [
    ClaudeMessage(
        role=ClaudeRole.USER,
        content="What's the weather in London?"
    )
]

# Generate response
response = adapter.generate(messages)
print(response)
```

### Function Calling
```python
from mcp_example.adapters.aws.claude import ClaudeAdapter, ClaudeMessage, ClaudeRole
from mcp_example.core.schema import FunctionDefinition

# Create adapter
adapter = ClaudeAdapter()

# Define function
weather_function = FunctionDefinition(
    name="get_weather",
    description="Get weather information",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "default": "celsius",
                "description": "Temperature unit",
            },
        },
        "required": ["location"],
    },
)

# Create messages
messages = [
    ClaudeMessage(
        role=ClaudeRole.USER,
        content="What's the weather in London?"
    )
]

# Generate response with function calling
response = adapter.generate(messages, functions=[weather_function])

# Extract function calls
function_calls = adapter.extract_function_calls(response)
print(function_calls)
```

### Streaming
```python
from mcp_example.adapters.aws.claude import ClaudeAdapter, ClaudeMessage, ClaudeRole

# Create adapter
adapter = ClaudeAdapter()

# Create messages
messages = [
    ClaudeMessage(
        role=ClaudeRole.USER,
        content="Write a story about a space explorer."
    )
]

# Generate streaming response
for chunk in adapter.generate_with_streaming(messages):
    print(chunk.content)
```

## Testing Approach
1. **Unit Tests**: Comprehensive unit tests for both adapters
   - Synchronous and asynchronous operation
   - Normal and streaming responses
   - Function call extraction
   - Message and parameter formatting

2. **Mocking**: Used MagicMock and AsyncMock to simulate AWS Bedrock responses
   - Simulated complete responses for non-streaming tests
   - Created mock async generators for streaming tests

3. **Error Handling**: Tests for error cases and edge conditions

## Future Improvements
1. **Enhanced Streaming**: Update streaming to handle complex delta updates from Claude
2. **Caching Integration**: Add integration with the existing caching mechanism
3. **Parameter Validation**: More robust validation of Claude-specific parameters
4. **Retry Handling**: Specialized retry logic for Claude-specific error scenarios
5. **Message History Management**: Tools for handling conversation contexts 