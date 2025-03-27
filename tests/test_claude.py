"""
Unit tests for Claude 3.7 integration adapter.
"""

import json
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from io import BytesIO

import boto3
import pytest
import pytest_asyncio

from mcp_example.adapters.aws.claude import (
    ClaudeAdapter,
    AsyncClaudeAdapter,
    ClaudeConfig,
    ClaudeMessage,
    ClaudeRole,
    ClaudeToolChoice
)
from mcp_example.adapters.aws.bedrock import BedrockClient, AsyncBedrockClient
from mcp_example.core.schema import FunctionDefinition, FunctionCall, StreamingChunk


class TestClaudeAdapter(unittest.TestCase):
    """Test cases for ClaudeAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_bedrock_client = MagicMock(spec=BedrockClient)
        
        self.config = ClaudeConfig(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=100,
            temperature=0.5,
        )
        
        self.adapter = ClaudeAdapter(
            bedrock_client=self.mock_bedrock_client,
            config=self.config,
        )
        
        # Sample function definitions
        self.functions = [
            FunctionDefinition(
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
            ),
        ]
        
        # Sample messages
        self.messages = [
            ClaudeMessage(
                role=ClaudeRole.USER,
                content="What's the weather in London?",
            ),
        ]
    
    def test_format_functions_as_tools(self):
        """Test formatting functions as Claude tools."""
        tools = self.adapter.format_functions_as_tools(self.functions)
        
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["type"], "function")
        self.assertEqual(tools[0]["function"]["name"], "get_weather")
        self.assertEqual(tools[0]["function"]["description"], "Get weather information")
        # Check that parameters are included without trying to access them as a dict
        self.assertIn("parameters", tools[0]["function"])
    
    def test_prepare_request_body_without_functions(self):
        """Test preparing request body without functions."""
        body = self.adapter._prepare_request_body(self.messages)
        
        self.assertEqual(body["anthropic_version"], self.config.anthropic_version)
        self.assertEqual(body["max_tokens"], 100)
        self.assertEqual(body["temperature"], 0.5)
        self.assertEqual(body["top_p"], 1.0)
        self.assertEqual(len(body["messages"]), 1)
        self.assertNotIn("tools", body)
    
    def test_prepare_request_body_with_functions(self):
        """Test preparing request body with functions."""
        body = self.adapter._prepare_request_body(self.messages, self.functions)
        
        self.assertIn("tools", body)
        self.assertEqual(len(body["tools"]), 1)
        self.assertEqual(body["tool_choice"], "auto")
    
    def test_parse_function_calls(self):
        """Test parsing function calls from response content."""
        content = [
            {
                "type": "text",
                "text": "I'll check the weather for you.",
            },
            {
                "type": "tool_use",
                "tool_use": {
                    "name": "get_weather",
                    "parameters": {
                        "location": "London",
                        "unit": "celsius",
                    },
                },
            },
        ]
        
        function_calls = self.adapter._parse_function_calls(content)
        
        self.assertEqual(len(function_calls), 1)
        self.assertEqual(function_calls[0].name, "get_weather")
        self.assertEqual(function_calls[0].parameters["location"], "London")
        self.assertEqual(function_calls[0].parameters["unit"], "celsius")
    
    def test_generate(self):
        """Test generating a response using Claude 3.7."""
        # Mock response
        response = {
            "id": "msg_01234567",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll check the weather for you.",
                },
                {
                    "type": "tool_use",
                    "tool_use": {
                        "name": "get_weather",
                        "parameters": {
                            "location": "London",
                            "unit": "celsius",
                        },
                    },
                },
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15,
            },
        }
        
        self.mock_bedrock_client.invoke_model.return_value = response
        
        result = self.adapter.generate(self.messages, self.functions)
        
        # Check call to bedrock client
        self.mock_bedrock_client.invoke_model.assert_called_once()
        args, kwargs = self.mock_bedrock_client.invoke_model.call_args
        self.assertEqual(kwargs["model_id"], self.config.model_id)
        
        # Check result
        self.assertEqual(result, response)
    
    def test_generate_with_streaming(self):
        """Test generating a streaming response using Claude 3.7."""
        # Mock streaming chunks
        chunks = [
            {
                "id": "chunk_01",
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "I'll check "},
                "content": "I'll check ",
                "usage": {},
            },
            {
                "id": "chunk_02",
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "the weather for you."},
                "content": "the weather for you.",
                "usage": {},
            },
            {
                "id": "chunk_03",
                "type": "message_stop",
                "delta": {},
                "content": "",
                "usage": {"input_tokens": 10, "output_tokens": 15},
            },
        ]
        
        self.mock_bedrock_client.invoke_model_with_response_stream.return_value = chunks
        
        result_chunks = list(self.adapter.generate_with_streaming(self.messages, self.functions))
        
        # Check call to bedrock client
        self.mock_bedrock_client.invoke_model_with_response_stream.assert_called_once()
        args, kwargs = self.mock_bedrock_client.invoke_model_with_response_stream.call_args
        self.assertEqual(kwargs["model_id"], self.config.model_id)
        
        # Check result chunks
        self.assertEqual(len(result_chunks), 3)
        self.assertFalse(result_chunks[0].is_final)
        self.assertFalse(result_chunks[1].is_final)
        self.assertTrue(result_chunks[2].is_final)
        self.assertEqual(result_chunks[0].status, "success")
    
    def test_extract_function_calls(self):
        """Test extracting function calls from Claude response."""
        response = {
            "id": "msg_01234567",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll check the weather for you.",
                },
                {
                    "type": "tool_use",
                    "tool_use": {
                        "name": "get_weather",
                        "parameters": {
                            "location": "London",
                            "unit": "celsius",
                        },
                    },
                },
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15,
            },
        }
        
        function_calls = self.adapter.extract_function_calls(response)
        
        self.assertEqual(len(function_calls), 1)
        self.assertEqual(function_calls[0].name, "get_weather")
        self.assertEqual(function_calls[0].parameters["location"], "London")
        self.assertEqual(function_calls[0].parameters["unit"], "celsius")


@pytest.mark.asyncio
class TestAsyncClaudeAdapter:
    """Test cases for AsyncClaudeAdapter."""
    
    @pytest_asyncio.fixture
    async def adapter(self):
        """Create adapter fixture with mocked bedrock client."""
        mock_bedrock_client = MagicMock(spec=AsyncBedrockClient)
        
        config = ClaudeConfig(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            max_tokens=100,
            temperature=0.5,
        )
        
        adapter = AsyncClaudeAdapter(
            bedrock_client=mock_bedrock_client,
            config=config,
        )
        
        # Store mock for later assertions
        adapter._mock_bedrock_client = mock_bedrock_client
        
        yield adapter
    
    @pytest_asyncio.fixture
    def functions(self):
        """Create sample function definitions."""
        return [
            FunctionDefinition(
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
            ),
        ]
    
    @pytest_asyncio.fixture
    def messages(self):
        """Create sample messages."""
        return [
            ClaudeMessage(
                role=ClaudeRole.USER,
                content="What's the weather in London?",
            ),
        ]
    
    async def test_generate(self, adapter, messages, functions):
        """Test generating a response using Claude 3.7 asynchronously."""
        # Mock response
        response = {
            "id": "msg_01234567",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll check the weather for you.",
                },
                {
                    "type": "tool_use",
                    "tool_use": {
                        "name": "get_weather",
                        "parameters": {
                            "location": "London",
                            "unit": "celsius",
                        },
                    },
                },
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15,
            },
        }
        
        adapter._mock_bedrock_client.invoke_model = AsyncMock(return_value=response)
        
        result = await adapter.generate(messages, functions)
        
        # Check call to bedrock client
        adapter._mock_bedrock_client.invoke_model.assert_called_once()
        args, kwargs = adapter._mock_bedrock_client.invoke_model.call_args
        assert kwargs["model_id"] == adapter.config.model_id
        
        # Check result
        assert result == response
    
    async def test_generate_with_streaming(self, adapter, messages, functions):
        """Test generating a streaming response using Claude 3.7 asynchronously."""
        # Mock streaming chunks
        chunks = [
            {
                "id": "chunk_01",
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "I'll check "},
                "content": "I'll check ",
                "usage": {},
            },
            {
                "id": "chunk_02",
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "the weather for you."},
                "content": "the weather for you.",
                "usage": {},
            },
            {
                "id": "chunk_03",
                "type": "message_stop",
                "delta": {},
                "content": "",
                "usage": {"input_tokens": 10, "output_tokens": 15},
            },
        ]
        
        # Create a mock that asynchronously yields chunks
        async def async_generator():
            for chunk in chunks:
                yield chunk
        
        adapter._mock_bedrock_client.invoke_model_with_response_stream = MagicMock(
            return_value=async_generator()
        )
        
        result_chunks = []
        async for chunk in adapter.generate_with_streaming(messages, functions):
            result_chunks.append(chunk)
        
        # Check call to bedrock client
        adapter._mock_bedrock_client.invoke_model_with_response_stream.assert_called_once()
        args, kwargs = adapter._mock_bedrock_client.invoke_model_with_response_stream.call_args
        assert kwargs["model_id"] == adapter.config.model_id
        
        # Check result chunks
        assert len(result_chunks) == 3
        assert not result_chunks[0].is_final
        assert not result_chunks[1].is_final
        assert result_chunks[2].is_final
        assert result_chunks[0].status == "success"
    
    async def test_extract_function_calls(self, adapter):
        """Test extracting function calls from Claude response."""
        response = {
            "id": "msg_01234567",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "I'll check the weather for you.",
                },
                {
                    "type": "tool_use",
                    "tool_use": {
                        "name": "get_weather",
                        "parameters": {
                            "location": "London",
                            "unit": "celsius",
                        },
                    },
                },
            ],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 15,
            },
        }
        
        function_calls = adapter.extract_function_calls(response)
        
        assert len(function_calls) == 1
        assert function_calls[0].name == "get_weather"
        assert function_calls[0].parameters["location"] == "London"
        assert function_calls[0].parameters["unit"] == "celsius" 