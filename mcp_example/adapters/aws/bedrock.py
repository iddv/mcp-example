"""
AWS Bedrock client for Model Context Protocol.

This module provides a client for interacting with AWS Bedrock models.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, AsyncIterator, BinaryIO, Iterator

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from pydantic import BaseModel, Field

from mcp_example.core.schema import StreamingChunk

logger = logging.getLogger(__name__)


class BedrockClientConfig(BaseModel):
    """Configuration for AWS Bedrock client."""
    
    region_name: str = Field(default="us-west-2", description="AWS region name")
    profile_name: Optional[str] = Field(default=None, description="AWS profile name")
    access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    session_token: Optional[str] = Field(default=None, description="AWS session token")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: float = Field(default=30.0, description="Timeout in seconds")
    endpoint_url: Optional[str] = Field(default=None, description="Custom endpoint URL")


class BedrockClient:
    """Client for AWS Bedrock API."""
    
    def __init__(
        self,
        config: Optional[BedrockClientConfig] = None,
    ):
        """
        Initialize Bedrock client.
        
        Args:
            config: Optional Bedrock client configuration
        """
        self.config = config or BedrockClientConfig()
        self.session = self._create_session()
        self.client = self._create_client()
    
    def _create_session(self) -> boto3.Session:
        """
        Create a boto3 session with the provided configuration.
        
        Returns:
            boto3.Session: Configured boto3 session
        """
        session_kwargs = {}
        
        if self.config.profile_name:
            session_kwargs["profile_name"] = self.config.profile_name
        
        if self.config.access_key_id and self.config.secret_access_key:
            session_kwargs["aws_access_key_id"] = self.config.access_key_id
            session_kwargs["aws_secret_access_key"] = self.config.secret_access_key
            
            if self.config.session_token:
                session_kwargs["aws_session_token"] = self.config.session_token
        
        return boto3.Session(**session_kwargs)
    
    def _create_client(self) -> boto3.Session.client:
        """
        Create a boto3 bedrock-runtime client.
        
        Returns:
            boto3.client: Configured bedrock-runtime client
        """
        client_kwargs = {
            "service_name": "bedrock-runtime",
            "region_name": self.config.region_name,
            "config": Config(
                retries={"max_attempts": self.config.max_retries},
                connect_timeout=self.config.timeout,
                read_timeout=self.config.timeout,
            ),
        }
        
        if self.config.endpoint_url:
            client_kwargs["endpoint_url"] = self.config.endpoint_url
        
        return self.session.client(**client_kwargs)
    
    def invoke_model(
        self,
        model_id: str,
        body: Dict[str, Any],
        accept: str = "application/json",
        content_type: str = "application/json",
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model.
        
        Args:
            model_id: Bedrock model ID
            body: Request body
            accept: Response content type
            content_type: Request content type
            
        Returns:
            Dict[str, Any]: Model response
            
        Raises:
            ClientError: If the Bedrock API request fails
        """
        try:
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                accept=accept,
                contentType=content_type,
            )
            
            response_body = json.loads(response["body"].read())
            return response_body
            
        except ClientError as e:
            logger.error(f"Error invoking Bedrock model: {str(e)}")
            raise
    
    def invoke_model_with_response_stream(
        self,
        model_id: str,
        body: Dict[str, Any],
        accept: str = "application/json",
        content_type: str = "application/json",
    ) -> Iterator[Dict[str, Any]]:
        """
        Invoke a Bedrock model with streaming response.
        
        Args:
            model_id: Bedrock model ID
            body: Request body
            accept: Response content type
            content_type: Request content type
            
        Yields:
            Dict[str, Any]: Streaming chunks of model response
            
        Raises:
            ClientError: If the Bedrock API request fails
        """
        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(body),
                accept=accept,
                contentType=content_type,
            )
            
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                yield chunk
                
        except ClientError as e:
            logger.error(f"Error invoking Bedrock model with streaming: {str(e)}")
            raise


class AsyncBedrockClient:
    """Asynchronous client for AWS Bedrock API."""
    
    def __init__(
        self,
        config: Optional[BedrockClientConfig] = None,
    ):
        """
        Initialize async Bedrock client.
        
        Args:
            config: Optional Bedrock client configuration
        """
        self.config = config or BedrockClientConfig()
        # Note: boto3 doesn't have native async support,
        # so we'll use the synchronous client in async context
        self.sync_client = BedrockClient(config=self.config)
    
    async def invoke_model(
        self,
        model_id: str,
        body: Dict[str, Any],
        accept: str = "application/json",
        content_type: str = "application/json",
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model asynchronously.
        
        Args:
            model_id: Bedrock model ID
            body: Request body
            accept: Response content type
            content_type: Request content type
            
        Returns:
            Dict[str, Any]: Model response
            
        Raises:
            ClientError: If the Bedrock API request fails
        """
        import asyncio
        
        return await asyncio.to_thread(
            self.sync_client.invoke_model,
            model_id=model_id,
            body=body,
            accept=accept,
            content_type=content_type,
        )
    
    async def invoke_model_with_response_stream(
        self,
        model_id: str,
        body: Dict[str, Any],
        accept: str = "application/json",
        content_type: str = "application/json",
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Invoke a Bedrock model with streaming response asynchronously.
        
        Args:
            model_id: Bedrock model ID
            body: Request body
            accept: Response content type
            content_type: Request content type
            
        Yields:
            Dict[str, Any]: Streaming chunks of model response
            
        Raises:
            ClientError: If the Bedrock API request fails
        """
        import asyncio
        
        # Create a generator that will yield chunks from the sync client
        def stream_generator():
            return self.sync_client.invoke_model_with_response_stream(
                model_id=model_id,
                body=body,
                accept=accept,
                content_type=content_type,
            )
        
        # Run the generator in a separate thread and yield chunks
        stream_gen = await asyncio.to_thread(stream_generator)
        
        for chunk in stream_gen:
            yield chunk 