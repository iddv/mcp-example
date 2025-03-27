"""
Tests for Claude 3.7 conversation flow example.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_example.adapters.aws.claude import AsyncClaudeAdapter, ClaudeMessage, ClaudeRole
from mcp_example.core.schema import FunctionCall, StreamingChunk
from mcp_example.examples.claude_conversation import conversation_with_tools


@pytest.fixture
def mock_claude_adapter():
    """Create a mock Claude adapter."""
    mock_adapter = AsyncMock(spec=AsyncClaudeAdapter)
    
    # Configure the mock for generate method
    claude_response = {
        "id": "msg_01234567890123456789",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I'll calculate that for you."
            },
            {
                "type": "tool_use",
                "tool_use": {
                    "name": "calculator",
                    "parameters": {
                        "operation": "add",
                        "a": 42,
                        "b": 7
                    }
                }
            }
        ]
    }
    mock_adapter.generate.return_value = claude_response
    
    # Configure the mock for extract_function_calls method
    function_call = FunctionCall(
        name="calculator",
        parameters={
            "operation": "add",
            "a": 42,
            "b": 7
        }
    )
    mock_adapter.extract_function_calls.return_value = [function_call]
    
    # Configure the mock for generate_with_streaming method
    async def mock_streaming(*args, **kwargs):
        yield StreamingChunk(
            id="msg_01234567890123456789",
            type="message_start",
            text="I'll calculate that for you."
        )
        yield StreamingChunk(
            id="msg_01234567890123456789",
            type="content_block_start",
            text=""
        )
        yield StreamingChunk(
            id="msg_01234567890123456789",
            type="content_block_delta",
            text="I'll calculate that for you."
        )
        yield StreamingChunk(
            id="msg_01234567890123456789",
            type="tool_use",
            function_calls=[function_call]
        )
    
    mock_adapter.generate_with_streaming.side_effect = mock_streaming
    
    return mock_adapter


@pytest.mark.asyncio
async def test_conversation_with_tools_non_streaming(mock_claude_adapter):
    """Test conversation flow with tools using non-streaming mode."""
    with patch('mcp_example.examples.claude_conversation.AsyncClaudeAdapter', return_value=mock_claude_adapter), \
         patch('mcp_example.examples.claude_conversation.register_all_tools'), \
         patch('mcp_example.examples.claude_conversation.registry.get_all_definitions'), \
         patch('mcp_example.core.executor.executor.execute_function'):
        
        # Execute with a simple test message
        await conversation_with_tools(["What's 42 + 7?"], streaming=False)
        
        # Verify Claude adapter was called with the message
        assert mock_claude_adapter.generate.called
        
        # Get the arguments the mock was called with
        args, kwargs = mock_claude_adapter.generate.call_args
        
        # Verify the message contains our test query
        messages = args[0]
        assert any(message.content == "What's 42 + 7?" for message in messages)
        
        # Verify function calls were extracted
        assert mock_claude_adapter.extract_function_calls.called


@pytest.mark.asyncio
async def test_conversation_with_tools_streaming(mock_claude_adapter):
    """Test conversation flow with tools using streaming mode."""
    with patch('mcp_example.examples.claude_conversation.AsyncClaudeAdapter', return_value=mock_claude_adapter), \
         patch('mcp_example.examples.claude_conversation.register_all_tools'), \
         patch('mcp_example.examples.claude_conversation.registry.get_all_definitions'), \
         patch('mcp_example.core.executor.executor.execute_function'):
        
        # Execute with a simple test message
        await conversation_with_tools(["What's 42 + 7?"], streaming=True)
        
        # Verify Claude streaming was called
        assert mock_claude_adapter.generate_with_streaming.called
        
        # Get the arguments the mock was called with
        args, kwargs = mock_claude_adapter.generate_with_streaming.call_args
        
        # Verify the message contains our test query
        messages = args[0]
        assert any(message.content == "What's 42 + 7?" for message in messages) 