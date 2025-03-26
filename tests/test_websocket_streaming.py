"""
Unit tests for WebSocket streaming functionality.
"""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from websockets.exceptions import WebSocketException

from mcp_example.adapters.http.client import AsyncMCPClient
from mcp_example.core.schema import StreamingChunk


@pytest.mark.asyncio
class TestWebSocketStreaming:
    """Tests for WebSocket streaming functionality."""

    @patch("websockets.connect")
    async def test_stream_function_success(self, mock_connect):
        """Test streaming a function successfully."""
        # Set up the mock WebSocket
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        # Set up the mock response
        chunk = StreamingChunk(
            chunk_id="test-chunk-1",
            call_id="test-call-1",
            content=8,
            is_final=True,
            status="success"
        )
        mock_websocket.receive_text.return_value = json.dumps(chunk.model_dump())
        
        # Create async iterator for the WebSocket
        mock_websocket.__aiter__.return_value = [json.dumps(chunk.model_dump())]

        # Create client and call stream_function
        client = AsyncMCPClient("http://test-server.com")
        chunks = []
        async for received_chunk in client.stream_function("calculator", {"operation": "add", "a": 5, "b": 3}):
            chunks.append(received_chunk)
        
        # Verify WebSocket connection was made correctly
        mock_connect.assert_called_once_with(
            "ws://test-server.com/api/functions/stream",
            extra_headers={},
            open_timeout=30.0
        )
        
        # Verify request was sent
        expected_request = {"name": "calculator", "parameters": {"operation": "add", "a": 5, "b": 3}}
        mock_websocket.send.assert_called_once_with(json.dumps(expected_request))
        
        # Verify response was processed correctly
        assert len(chunks) == 1
        assert chunks[0].chunk_id == "test-chunk-1"
        assert chunks[0].call_id == "test-call-1"
        assert chunks[0].content == 8
        assert chunks[0].is_final is True
        assert chunks[0].status == "success"
        
        # Cleanup
        await client.close()

    @patch("websockets.connect")
    async def test_stream_tool_success(self, mock_connect):
        """Test streaming a tool successfully."""
        # Set up the mock WebSocket
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        # Set up the mock response
        chunk = StreamingChunk(
            chunk_id="test-chunk-1",
            call_id="test-call-1",
            content="HELLO WORLD",
            is_final=True,
            status="success"
        )
        
        # Create async iterator for the WebSocket
        mock_websocket.__aiter__.return_value = [json.dumps(chunk.model_dump())]

        # Create client and call stream_tool
        client = AsyncMCPClient("http://test-server.com")
        chunks = []
        async for received_chunk in client.stream_tool("text", {"operation": "to_uppercase", "text": "hello world"}):
            chunks.append(received_chunk)
        
        # Verify WebSocket connection was made correctly
        mock_connect.assert_called_once_with(
            "ws://test-server.com/api/tools/stream",
            extra_headers={},
            open_timeout=30.0
        )
        
        # Verify request was sent
        expected_request = {
            "id": unittest.mock.ANY,  # We don't know the generated UUID
            "function": {
                "name": "text",
                "parameters": {"operation": "to_uppercase", "text": "hello world"}
            }
        }
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data["function"] == expected_request["function"]
        assert "id" in sent_data
        
        # Verify response was processed correctly
        assert len(chunks) == 1
        assert chunks[0].chunk_id == "test-chunk-1"
        assert chunks[0].call_id == "test-call-1"
        assert chunks[0].content == "HELLO WORLD"
        assert chunks[0].is_final is True
        assert chunks[0].status == "success"
        
        # Cleanup
        await client.close()

    @patch("websockets.connect")
    async def test_stream_function_error(self, mock_connect):
        """Test handling errors in function streaming."""
        # Set up the mock WebSocket
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        # Set up the mock error response
        error_chunk = StreamingChunk(
            chunk_id="test-chunk-1",
            call_id="test-call-1",
            content=None,
            is_final=True,
            error="Function not found",
            status="error"
        )
        
        # Create async iterator for the WebSocket
        mock_websocket.__aiter__.return_value = [json.dumps(error_chunk.model_dump())]

        # Create client and call stream_function
        client = AsyncMCPClient("http://test-server.com")
        chunks = []
        async for received_chunk in client.stream_function("nonexistent", {"param": "value"}):
            chunks.append(received_chunk)
        
        # Verify error response was processed correctly
        assert len(chunks) == 1
        assert chunks[0].chunk_id == "test-chunk-1"
        assert chunks[0].call_id == "test-call-1"
        assert chunks[0].content is None
        assert chunks[0].is_final is True
        assert chunks[0].error == "Function not found"
        assert chunks[0].status == "error"
        
        # Cleanup
        await client.close()

    @patch("websockets.connect")
    async def test_stream_connection_failure(self, mock_connect):
        """Test handling WebSocket connection failures."""
        # Set up the mock to raise an exception
        mock_connect.return_value.__aenter__.side_effect = WebSocketException("Connection failed")

        # Create client and call stream_function
        client = AsyncMCPClient("http://test-server.com", max_retries=0)
        
        # Verify that the exception is raised
        with pytest.raises(WebSocketException):
            async for _ in client.stream_function("calculator", {"operation": "add", "a": 5, "b": 3}):
                pass
        
        # Cleanup
        await client.close()

    @patch("websockets.connect")
    async def test_stream_multiple_chunks(self, mock_connect):
        """Test receiving multiple chunks in a stream."""
        # Set up the mock WebSocket
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        # Set up multiple chunks
        chunk1 = StreamingChunk(
            chunk_id="test-chunk-1",
            call_id="test-call-1",
            content="partial result 1",
            is_final=False,
            status="success"
        )
        
        chunk2 = StreamingChunk(
            chunk_id="test-chunk-2",
            call_id="test-call-1",
            content="partial result 2",
            is_final=False,
            status="success"
        )
        
        chunk3 = StreamingChunk(
            chunk_id="test-chunk-3",
            call_id="test-call-1",
            content="final result",
            is_final=True,
            status="success"
        )
        
        # Create async iterator for the WebSocket
        mock_websocket.__aiter__.return_value = [
            json.dumps(chunk1.model_dump()),
            json.dumps(chunk2.model_dump()),
            json.dumps(chunk3.model_dump())
        ]

        # Create client and call stream_function
        client = AsyncMCPClient("http://test-server.com")
        chunks = []
        async for received_chunk in client.stream_function("somefunction", {"param": "value"}):
            chunks.append(received_chunk)
        
        # Verify all chunks were received
        assert len(chunks) == 3
        
        assert chunks[0].chunk_id == "test-chunk-1"
        assert chunks[0].is_final is False
        assert chunks[0].content == "partial result 1"
        
        assert chunks[1].chunk_id == "test-chunk-2"
        assert chunks[1].is_final is False
        assert chunks[1].content == "partial result 2"
        
        assert chunks[2].chunk_id == "test-chunk-3"
        assert chunks[2].is_final is True
        assert chunks[2].content == "final result"
        
        # Cleanup
        await client.close() 