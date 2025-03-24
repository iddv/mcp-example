"""
FastAPI server for Model Context Protocol.

This module provides a FastAPI server for MCP tool execution.
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Union

import fastapi
from fastapi import Body, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from mcp_example.core.executor import ToolExecutor, executor
from mcp_example.core.registry import registry
from mcp_example.core.schema import (
    FunctionCall,
    FunctionDefinition,
    FunctionList,
    FunctionResponse,
    Tool,
    ToolCall,
    ToolResponse,
)
from mcp_example.tools import register_all_tools

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Example Server",
    description="Model Context Protocol example server",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models for API endpoints

class FunctionCallRequest(BaseModel):
    """Request model for function call."""

    name: str
    parameters: Dict[str, Any]


class ToolCallRequest(BaseModel):
    """Request model for tool call."""

    id: Optional[str] = None
    function: FunctionCallRequest


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: Optional[Dict[str, Any]] = None


# Simple API key authentication
API_KEYS = {"test-key": "test-user"}


def verify_api_key(request: Request) -> str:
    """
    Verify API key from request header.

    Args:
        request: FastAPI request

    Returns:
        User ID associated with the API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    
    user_id = API_KEYS.get(api_key)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return user_id


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Register all tools on startup."""
    register_all_tools()
    logger.info(f"Registered {len(registry.list_tools())} tools")


# API routes

@app.get("/api/functions", response_model=FunctionList)
async def list_functions() -> FunctionList:
    """
    List all available functions.

    Returns:
        List of function definitions
    """
    return FunctionList(functions=registry.list_function_definitions())


@app.get("/api/functions/{name}", response_model=FunctionDefinition)
async def get_function(name: str) -> FunctionDefinition:
    """
    Get a function definition by name.

    Args:
        name: Name of the function

    Returns:
        Function definition

    Raises:
        HTTPException: If function not found
    """
    func_def = registry.get_function_definition(name)
    if not func_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function '{name}' not found",
        )
    return func_def


@app.post("/api/functions/call", response_model=FunctionResponse)
async def call_function(
    call: FunctionCallRequest,
    user_id: str = Depends(verify_api_key),
) -> FunctionResponse:
    """
    Call a function.

    Args:
        call: Function call request
        user_id: User ID from API key authentication

    Returns:
        Function response
    """
    logger.info(f"Function call from user {user_id}: {call.name}")
    
    func_call = FunctionCall(name=call.name, parameters=call.parameters)
    response = executor.execute_function(func_call)
    
    return response


@app.post("/api/tools/call", response_model=ToolResponse)
async def call_tool(
    call: ToolCallRequest,
    user_id: str = Depends(verify_api_key),
) -> ToolResponse:
    """
    Call a tool.

    Args:
        call: Tool call request
        user_id: User ID from API key authentication

    Returns:
        Tool response
    """
    logger.info(f"Tool call from user {user_id}: {call.function.name}")
    
    # Generate ID if not provided
    call_id = call.id or str(uuid.uuid4())
    
    # Create tool call
    tool_call = ToolCall(
        id=call_id,
        function=FunctionCall(
            name=call.function.name,
            parameters=call.function.parameters,
        ),
    )
    
    # Execute tool call
    response = executor.execute_tool_call(tool_call)
    
    return response


@app.post("/api/execute", response_model=Union[FunctionResponse, List[FunctionResponse]])
async def execute_from_text(
    request: Dict[str, Any] = Body(...),
    user_id: str = Depends(verify_api_key),
) -> Union[FunctionResponse, List[FunctionResponse]]:
    """
    Execute a function call from text.

    Args:
        request: Request body containing text
        user_id: User ID from API key authentication

    Returns:
        Function response or list of responses

    Raises:
        HTTPException: If text is missing or no function call found
    """
    text = request.get("text")
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is required",
        )
    
    logger.info(f"Execute from text request from user {user_id}")
    
    response = executor.execute_from_text(text)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No function call found in text",
        )
    
    return response


# Error handling

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)},
    ) 