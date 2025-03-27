"""
Claude 3.7 integration for AWS Bedrock.

This module provides adapters for using Claude 3.7 model via AWS Bedrock with the Model Context Protocol.
"""

import json
import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union, AsyncIterator, Iterator

from pydantic import BaseModel, Field, validator

from mcp_example.adapters.aws.bedrock import BedrockClient, AsyncBedrockClient
from mcp_example.core.schema import FunctionCall, FunctionDefinition, StreamingChunk

logger = logging.getLogger(__name__)


class ClaudeRole(str, Enum):
    """Role for Claude messages."""
    
    USER = "user"
    ASSISTANT = "assistant"


class ClaudeMessage(BaseModel):
    """Message for Claude API."""
    
    role: ClaudeRole = Field(..., description="Role of the message sender")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="Message content")
    
    @validator("content")
    def validate_content(cls, v):
        """Validate content format."""
        if isinstance(v, str):
            return v
        elif isinstance(v, list):
            for item in v:
                if not isinstance(item, dict):
                    raise ValueError("Content items must be dictionaries")
                if "type" not in item:
                    raise ValueError("Content items must have 'type' field")
            return v
        else:
            raise ValueError("Content must be either string or list of dictionaries")


class ClaudeToolChoice(str, Enum):
    """Tool choice options for Claude."""
    
    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


class ClaudeConfig(BaseModel):
    """Configuration for Claude API requests."""
    
    model_id: str = Field(
        default="anthropic.claude-3-haiku-20240307-v1:0",
        description="Claude model ID"
    )
    max_tokens: int = Field(default=1024, description="Maximum number of tokens to generate")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    top_p: float = Field(default=1.0, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter")
    stop_sequences: Optional[List[str]] = Field(default=None, description="Sequences that stop generation")
    anthropic_version: str = Field(default="bedrock-2023-05-31", description="Anthropic API version")
    tool_choice: ClaudeToolChoice = Field(default=ClaudeToolChoice.AUTO, description="Tool choice option")


class ClaudeAdapter:
    """Adapter for Claude 3.7 model via AWS Bedrock."""
    
    def __init__(
        self,
        bedrock_client: Optional[BedrockClient] = None,
        config: Optional[ClaudeConfig] = None,
    ):
        """
        Initialize Claude adapter.
        
        Args:
            bedrock_client: Optional BedrockClient instance
            config: Optional Claude configuration
        """
        self.bedrock_client = bedrock_client or BedrockClient()
        self.config = config or ClaudeConfig()
    
    def format_functions_as_tools(self, functions: List[FunctionDefinition]) -> List[Dict[str, Any]]:
        """
        Format function definitions as Claude tools.
        
        Args:
            functions: List of function definitions
            
        Returns:
            List[Dict[str, Any]]: Formatted tools for Claude API
        """
        tools = []
        
        for function in functions:
            tool = {
                "type": "function",
                "function": {
                    "name": function.name,
                    "description": function.description,
                    "parameters": function.parameters,
                }
            }
            tools.append(tool)
        
        return tools
    
    def _prepare_request_body(
        self,
        messages: List[ClaudeMessage],
        functions: Optional[List[FunctionDefinition]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare request body for Claude API.
        
        Args:
            messages: List of messages
            functions: Optional list of function definitions to include as tools
            
        Returns:
            Dict[str, Any]: Formatted request body
        """
        body = {
            "anthropic_version": self.config.anthropic_version,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "messages": [m.model_dump() for m in messages],
        }
        
        # Add optional parameters if specified
        if self.config.top_k is not None:
            body["top_k"] = self.config.top_k
            
        if self.config.stop_sequences:
            body["stop_sequences"] = self.config.stop_sequences
        
        # Add tools if functions are provided
        if functions:
            body["tools"] = self.format_functions_as_tools(functions)
            body["tool_choice"] = self.config.tool_choice
        
        return body
    
    def _parse_function_calls(self, content: List[Dict[str, Any]]) -> List[FunctionCall]:
        """
        Parse function calls from Claude response content.
        
        Args:
            content: Response content from Claude
            
        Returns:
            List[FunctionCall]: Parsed function calls
        """
        function_calls = []
        
        for item in content:
            if item.get("type") == "tool_use":
                tool = item.get("tool_use", {})
                name = tool.get("name", "")
                parameters = tool.get("parameters", {})
                
                function_call = FunctionCall(
                    name=name,
                    parameters=parameters,
                )
                function_calls.append(function_call)
        
        return function_calls
    
    def generate(
        self,
        messages: List[ClaudeMessage],
        functions: Optional[List[FunctionDefinition]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response using Claude 3.7.
        
        Args:
            messages: List of messages for the conversation
            functions: Optional list of function definitions to include as tools
            
        Returns:
            Dict[str, Any]: Claude response
            
        Raises:
            Exception: If the API request fails
        """
        body = self._prepare_request_body(messages, functions)
        
        response = self.bedrock_client.invoke_model(
            model_id=self.config.model_id,
            body=body,
        )
        
        return response
    
    def generate_with_streaming(
        self,
        messages: List[ClaudeMessage],
        functions: Optional[List[FunctionDefinition]] = None,
    ) -> Iterator[StreamingChunk]:
        """
        Generate a streaming response using Claude 3.7.
        
        Args:
            messages: List of messages for the conversation
            functions: Optional list of function definitions to include as tools
            
        Yields:
            StreamingChunk: Chunks of Claude response
            
        Raises:
            Exception: If the API request fails
        """
        body = self._prepare_request_body(messages, functions)
        call_id = str(uuid.uuid4())
        
        # Track partial content to accumulate function calls
        partial_content = ""
        partial_tool_calls = []
        
        for chunk in self.bedrock_client.invoke_model_with_response_stream(
            model_id=self.config.model_id,
            body=body,
        ):
            # Extract relevant data from Bedrock chunk
            is_final = chunk.get("type") == "message_stop"
            error = None
            status = "success"
            
            if "error" in chunk:
                error = chunk.get("error", {}).get("message", "Unknown error")
                status = "error"
                is_final = True
            
            # Extract content from chunk
            content = ""
            
            # Handle different chunk types
            if chunk.get("type") == "content_block_delta":
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    content = delta.get("text", "")
                    partial_content += content
                elif delta.get("type") == "tool_use":
                    # Store tool use delta for later processing
                    partial_tool_calls.append(delta.get("tool_use", {}))
            elif chunk.get("type") == "content_block_start":
                block = chunk.get("content_block", {})
                if block.get("type") == "text":
                    content = block.get("text", "")
                    partial_content += content
                elif block.get("type") == "tool_use":
                    # Store tool use for later processing
                    partial_tool_calls.append(block.get("tool_use", {}))
            
            # For message_stop, include any parsed function calls
            function_calls = []
            if is_final and partial_tool_calls:
                for tool_use in partial_tool_calls:
                    name = tool_use.get("name", "")
                    parameters = tool_use.get("parameters", {})
                    
                    if name:
                        function_calls.append(FunctionCall(
                            name=name,
                            parameters=parameters,
                        ))
            
            # Create StreamingChunk with required fields
            streaming_chunk = StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                call_id=call_id,
                content=chunk.get("content", content),  # Use existing content field if available
                is_final=is_final,
                error=error,
                status=status
            )
            
            # If final chunk, include full content and any function calls
            if is_final and partial_content:
                streaming_chunk.content = partial_content
            
            yield streaming_chunk
    
    def extract_function_calls(self, response: Dict[str, Any]) -> List[FunctionCall]:
        """
        Extract function calls from Claude response.
        
        Args:
            response: Claude response
            
        Returns:
            List[FunctionCall]: Extracted function calls
        """
        content = response.get("content", [])
        if isinstance(content, list):
            return self._parse_function_calls(content)
        return []


class AsyncClaudeAdapter:
    """Asynchronous adapter for Claude 3.7 model via AWS Bedrock."""
    
    def __init__(
        self,
        bedrock_client: Optional[AsyncBedrockClient] = None,
        config: Optional[ClaudeConfig] = None,
    ):
        """
        Initialize async Claude adapter.
        
        Args:
            bedrock_client: Optional AsyncBedrockClient instance
            config: Optional Claude configuration
        """
        self.bedrock_client = bedrock_client or AsyncBedrockClient()
        self.config = config or ClaudeConfig()
        self.sync_adapter = ClaudeAdapter(config=config)
    
    async def generate(
        self,
        messages: List[ClaudeMessage],
        functions: Optional[List[FunctionDefinition]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response using Claude 3.7 asynchronously.
        
        Args:
            messages: List of messages for the conversation
            functions: Optional list of function definitions to include as tools
            
        Returns:
            Dict[str, Any]: Claude response
            
        Raises:
            Exception: If the API request fails
        """
        body = self.sync_adapter._prepare_request_body(messages, functions)
        
        response = await self.bedrock_client.invoke_model(
            model_id=self.config.model_id,
            body=body,
        )
        
        return response
    
    async def generate_with_streaming(
        self,
        messages: List[ClaudeMessage],
        functions: Optional[List[FunctionDefinition]] = None,
    ) -> AsyncIterator[StreamingChunk]:
        """
        Generate a streaming response using Claude 3.7 asynchronously.
        
        Args:
            messages: List of messages for the conversation
            functions: Optional list of function definitions to include as tools
            
        Yields:
            StreamingChunk: Chunks of Claude response
            
        Raises:
            Exception: If the API request fails
        """
        body = self.sync_adapter._prepare_request_body(messages, functions)
        call_id = str(uuid.uuid4())
        
        # Track partial content to accumulate function calls
        partial_content = ""
        partial_tool_calls = []
        
        async for chunk in self.bedrock_client.invoke_model_with_response_stream(
            model_id=self.config.model_id,
            body=body,
        ):
            # Extract relevant data from Bedrock chunk
            is_final = chunk.get("type") == "message_stop"
            error = None
            status = "success"
            
            if "error" in chunk:
                error = chunk.get("error", {}).get("message", "Unknown error")
                status = "error"
                is_final = True
            
            # Extract content from chunk
            content = ""
            
            # Handle different chunk types
            if chunk.get("type") == "content_block_delta":
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    content = delta.get("text", "")
                    partial_content += content
                elif delta.get("type") == "tool_use":
                    # Store tool use delta for later processing
                    partial_tool_calls.append(delta.get("tool_use", {}))
            elif chunk.get("type") == "content_block_start":
                block = chunk.get("content_block", {})
                if block.get("type") == "text":
                    content = block.get("text", "")
                    partial_content += content
                elif block.get("type") == "tool_use":
                    # Store tool use for later processing
                    partial_tool_calls.append(block.get("tool_use", {}))
            
            # For message_stop, include any parsed function calls
            function_calls = []
            if is_final and partial_tool_calls:
                for tool_use in partial_tool_calls:
                    name = tool_use.get("name", "")
                    parameters = tool_use.get("parameters", {})
                    
                    if name:
                        function_calls.append(FunctionCall(
                            name=name,
                            parameters=parameters,
                        ))
            
            # Create StreamingChunk with required fields
            streaming_chunk = StreamingChunk(
                chunk_id=str(uuid.uuid4()),
                call_id=call_id,
                content=chunk.get("content", content),  # Use existing content field if available
                is_final=is_final,
                error=error,
                status=status
            )
            
            # If final chunk, include full content and any function calls
            if is_final and partial_content:
                streaming_chunk.content = partial_content
            
            yield streaming_chunk
    
    def extract_function_calls(self, response: Dict[str, Any]) -> List[FunctionCall]:
        """
        Extract function calls from Claude response.
        
        Args:
            response: Claude response
            
        Returns:
            List[FunctionCall]: Extracted function calls
        """
        return self.sync_adapter.extract_function_calls(response) 