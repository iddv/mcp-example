# Claude 3.7 Conversation Flow Implementation

## Overview and Purpose

The Claude 3.7 conversation flow implementation demonstrates how to use the AWS Bedrock Claude 3.7 model with the Model Context Protocol (MCP) to have interactive conversations with tool usage. This component showcases how to:

1. Initialize a conversation with Claude 3.7
2. Send user messages and receive model responses
3. Handle tool invocations by Claude 3.7
4. Execute tools and update the conversation with tool results
5. Support both streaming and non-streaming modes of interaction

This implementation acts as a bridge between the high-level Claude 3.7 API and the MCP tool ecosystem, allowing Claude to access and use tools registered in the system.

## Implementation Details

### Key Components

1. **AsyncClaudeAdapter**: Handles communication with AWS Bedrock Claude 3.7 model, supporting both streaming and non-streaming response modes.

2. **Conversation Management**: Maintains the conversation history as a list of `ClaudeMessage` objects with proper role assignments.

3. **Tool Integration**: Converts registered MCP tools into Claude-compatible tool definitions and handles the extraction and execution of tool calls from Claude's responses.

4. **Tool Result Incorporation**: Adds tool results back into the conversation context, allowing Claude to reference previous tool outputs.

### Implementation Flow

1. **Initialization**:
   - Register all available tools
   - Create Claude adapter with configured settings
   - Initialize conversation with system message explaining available tools

2. **User Message Processing**:
   - Add user message to conversation history
   - Send updated conversation to Claude with tool definitions

3. **Response Handling**:
   - For streaming mode: Process chunks as they arrive, handling both text and function calls
   - For non-streaming mode: Process the complete response, extracting text and function calls

4. **Tool Execution**:
   - When Claude invokes a tool, extract the function call details
   - Execute the function using the MCP executor
   - Add the tool result back to the conversation

5. **Continuation**:
   - If tools were used, get a follow-up response from Claude that incorporates tool results
   - Add Claude's response to conversation history
   - Continue with next user message

## Example Usage

```python
import asyncio
from mcp_example.examples.claude_conversation import conversation_with_tools

# Define user messages for the conversation
messages = [
    "What's 42 + 7?",
    "Can you convert 'hello world' to uppercase?",
    "Tell me the result of multiplying 12 by 15, then format it as a dollar amount."
]

# Run the conversation with streaming enabled
asyncio.run(conversation_with_tools(messages, streaming=True))
```

### Sample Output

```
=== Claude 3.7 Conversation with Tool Usage ===

User: What's 42 + 7?

Claude (streaming): To calculate 42 + 7, I'll use the calculator tool.

[Using tool: calculator]
Parameters: {'operation': 'add', 'a': 42, 'b': 7}
Tool result: 49

The answer is 49.

User: Can you convert 'hello world' to uppercase?

Claude (streaming): I'll convert "hello world" to uppercase using the text tool.

[Using tool: text]
Parameters: {'operation': 'to_uppercase', 'text': 'hello world'}
Tool result: HELLO WORLD

The uppercase version of "hello world" is "HELLO WORLD".
```

## Testing Approach

Testing for the Claude conversation implementation should focus on:

1. **Unit Tests**:
   - Test the conversion of MCP tool definitions to Claude-compatible format
   - Test the extraction of function calls from Claude responses
   - Test the handling of different response types (text-only, function calls, mixed)

2. **Integration Tests**:
   - Test the end-to-end conversation flow with mock Claude responses
   - Test the proper handling of conversation context through multiple turns
   - Test both streaming and non-streaming modes

3. **Mock Testing**:
   - Use mock AWS Bedrock client to avoid actual API calls during testing
   - Create mock Claude responses that include function calls and text

4. **Error Handling Tests**:
   - Test behavior when Claude returns malformed responses
   - Test handling of errors during tool execution
   - Test recovery mechanisms when AWS API calls fail

## Future Improvements

1. **Authentication Handling**: Add support for different AWS authentication methods.

2. **Model Configuration**: Provide more detailed configuration options for the Claude model.

3. **Response Filtering**: Implement filtering of sensitive information in responses.

4. **Performance Optimization**: Add caching for frequent tool calls to improve response time.

5. **Conversation Management**: Add support for longer conversations with context window management.

6. **Error Recovery**: Implement more sophisticated error recovery mechanisms for failed tool calls.

7. **Multi-Model Support**: Extend the implementation to support other models besides Claude 3.7.

8. **Tool Discovery**: Add dynamic tool discovery for Claude based on conversation context. 