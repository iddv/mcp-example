"""
Core schema definitions for Model Context Protocol (MCP).

This module defines the JSON schemas for function definitions, function calls,
and function responses according to the Model Context Protocol.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

# Function Definition Schema


class PropertySchema(BaseModel):
    """Schema for a property in a function parameter."""

    type: str = Field(..., description="The type of the property")
    description: str = Field(..., description="Description of the property")
    enum: Optional[List[str]] = Field(None, description="Possible values for the property")
    format: Optional[str] = Field(None, description="Format of the property")
    default: Optional[Any] = Field(None, description="Default value for the property")
    items: Optional[Dict[str, Any]] = Field(
        None, description="Schema for array items if type is array"
    )
    properties: Optional[Dict[str, "PropertySchema"]] = Field(
        None, description="Nested properties if type is object"
    )
    required: Optional[List[str]] = Field(
        None, description="Required properties if type is object"
    )


class ParameterSchema(BaseModel):
    """Schema for function parameters."""

    type: str = Field("object", description="The type of the parameters object")
    properties: Dict[str, PropertySchema] = Field(
        ..., description="Properties of the parameters object"
    )
    required: Optional[List[str]] = Field(
        None, description="Required properties in the parameters object"
    )


class FunctionDefinition(BaseModel):
    """Definition of a function that can be called by an LLM."""

    name: str = Field(..., description="The name of the function")
    description: str = Field(..., description="Description of what the function does")
    parameters: ParameterSchema = Field(
        ..., description="Parameters accepted by the function"
    )


# Function Call Schema


class FunctionParameters(BaseModel):
    """Parameters for a function call."""

    model_config = {"extra": "allow"}
    
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class FunctionCall(BaseModel):
    """A function call from an LLM."""

    name: str = Field(..., description="The name of the function to call")
    parameters: Dict[str, Any] = Field(
        ..., description="Parameters for the function call"
    )


# Function Response Schema


class FunctionResponse(BaseModel):
    """Response from a function call."""

    result: Any = Field(..., description="Result of the function call")
    error: Optional[str] = Field(None, description="Error message if function call failed")
    status: Literal["success", "error"] = Field(
        "success", description="Status of the function call"
    )


# Function List Schema


class FunctionList(BaseModel):
    """List of available functions."""

    functions: List[FunctionDefinition] = Field(
        ..., description="List of available functions"
    )


# Tool Definition and Response


class Tool(BaseModel):
    """Definition of a tool that can be called."""

    function: FunctionDefinition = Field(..., description="Function definition for the tool")


class ToolCall(BaseModel):
    """A tool call request."""

    id: str = Field(..., description="Unique identifier for the tool call")
    function: FunctionCall = Field(..., description="Function to call")


class ToolResponse(BaseModel):
    """Response from a tool call."""

    id: str = Field(..., description="Identifier matching the tool call ID")
    function: FunctionResponse = Field(..., description="Function response")


# Streaming Response Schema

class StreamingChunk(BaseModel):
    """Chunk of a streaming response."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    call_id: str = Field(..., description="ID of the function or tool call")
    content: Any = Field(..., description="Content of the chunk")
    is_final: bool = Field(False, description="Whether this is the final chunk")
    error: Optional[str] = Field(None, description="Error message if an error occurred")
    status: Literal["success", "error"] = Field(
        "success", description="Status of the chunk"
    ) 