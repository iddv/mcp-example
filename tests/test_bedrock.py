"""
Unit tests for AWS Bedrock client.
"""

import json
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from io import BytesIO

import boto3
import pytest
import pytest_asyncio

from mcp_example.adapters.aws.bedrock import BedrockClient, AsyncBedrockClient, BedrockClientConfig


class MockResponse:
    """Mock response for boto3 client."""
    
    def __init__(self, body):
        self.body = BytesIO(json.dumps(body).encode())
    
    def read(self):
        return self.body.read()


class MockStreamingResponse:
    """Mock streaming response for boto3 client."""
    
    def __init__(self, chunks):
        self.chunks = chunks
        
    def __iter__(self):
        for chunk in self.chunks:
            yield {"chunk": {"bytes": json.dumps(chunk).encode()}}


class TestBedrockClient(unittest.TestCase):
    """Test cases for BedrockClient."""
    
    @patch("boto3.Session")
    def setUp(self, mock_session):
        """Set up test fixtures."""
        self.mock_session = mock_session
        self.mock_client = MagicMock()
        mock_session.return_value.client.return_value = self.mock_client
        
        self.config = BedrockClientConfig(
            region_name="us-east-1",
            profile_name="test-profile",
            max_retries=2,
            timeout=10.0,
        )
        
        self.client = BedrockClient(config=self.config)
    
    def test_init(self):
        """Test initializing the client."""
        # Check that session was created with correct profile
        self.mock_session.assert_called_once_with(profile_name="test-profile")
        
        # Check that client was created with correct parameters
        self.mock_session.return_value.client.assert_called_once_with(
            service_name="bedrock-runtime",
            region_name="us-east-1",
            config=unittest.mock.ANY,  # Checking exact config is complex
        )
    
    def test_invoke_model(self):
        """Test invoking a model."""
        # Mock response
        model_response = {"generated_text": "Hello, world!"}
        mock_response = {"body": MockResponse(model_response)}
        self.mock_client.invoke_model.return_value = mock_response
        
        # Test parameters
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        body = {"prompt": "Hello", "max_tokens": 100}
        
        # Call method
        response = self.client.invoke_model(
            model_id=model_id,
            body=body,
        )
        
        # Check call parameters
        self.mock_client.invoke_model.assert_called_once_with(
            modelId=model_id,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json",
        )
        
        # Check response
        self.assertEqual(response, model_response)
    
    def test_invoke_model_with_response_stream(self):
        """Test invoking a model with streaming response."""
        # Mock response chunks
        chunks = [
            {"generated_text": "Hello"},
            {"generated_text": ", world"},
            {"generated_text": "!"},
        ]
        
        mock_response = {"body": MockStreamingResponse(chunks)}
        self.mock_client.invoke_model_with_response_stream.return_value = mock_response
        
        # Test parameters
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        body = {"prompt": "Hello", "max_tokens": 100}
        
        # Call method and collect chunks
        response_chunks = list(self.client.invoke_model_with_response_stream(
            model_id=model_id,
            body=body,
        ))
        
        # Check call parameters
        self.mock_client.invoke_model_with_response_stream.assert_called_once_with(
            modelId=model_id,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json",
        )
        
        # Check response chunks
        self.assertEqual(response_chunks, chunks)


@pytest.mark.asyncio
class TestAsyncBedrockClient:
    """Test cases for AsyncBedrockClient."""
    
    @pytest_asyncio.fixture
    async def client(self):
        """Create client fixture with mocked boto3 session."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client
            
            config = BedrockClientConfig(
                region_name="us-east-1",
                profile_name="test-profile",
                max_retries=2,
                timeout=10.0,
            )
            
            client = AsyncBedrockClient(config=config)
            
            # Store mock objects for later assertions
            client._mock_session = mock_session
            client._mock_client = mock_client
            
            yield client
    
    async def test_invoke_model(self, client):
        """Test invoking a model asynchronously."""
        # Mock response
        model_response = {"generated_text": "Hello, world!"}
        mock_response = {"body": MockResponse(model_response)}
        client.sync_client.invoke_model = MagicMock(return_value=model_response)
        
        # Test parameters
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        body = {"prompt": "Hello", "max_tokens": 100}
        
        # Call method
        response = await client.invoke_model(
            model_id=model_id,
            body=body,
        )
        
        # Check call parameters
        client.sync_client.invoke_model.assert_called_once_with(
            model_id=model_id,
            body=body,
            accept="application/json",
            content_type="application/json",
        )
        
        # Check response
        assert response == model_response
    
    async def test_invoke_model_with_response_stream(self, client):
        """Test invoking a model with streaming response asynchronously."""
        # Mock response chunks
        chunks = [
            {"generated_text": "Hello"},
            {"generated_text": ", world"},
            {"generated_text": "!"},
        ]
        
        # Create a mock that returns an iterator over chunks
        client.sync_client.invoke_model_with_response_stream = MagicMock(return_value=chunks)
        
        # Test parameters
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        body = {"prompt": "Hello", "max_tokens": 100}
        
        # Call method and collect chunks
        response_chunks = []
        async for chunk in client.invoke_model_with_response_stream(
            model_id=model_id,
            body=body,
        ):
            response_chunks.append(chunk)
        
        # Check call parameters
        client.sync_client.invoke_model_with_response_stream.assert_called_once_with(
            model_id=model_id,
            body=body,
            accept="application/json",
            content_type="application/json",
        )
        
        # Check response chunks
        assert response_chunks == chunks 