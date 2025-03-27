# MCP Server API Documentation

## Overview

The MCP Server provides a REST API and WebSocket endpoints for interacting with Model Context Protocol tools. This document outlines all available endpoints, request/response formats, authentication requirements, and includes usage examples.

## Authentication

The API uses a simple API key authentication method:

- Include the `X-API-Key` header in all HTTP requests
- Default test key: `test-key`
- WebSocket connections do not require authentication headers

## REST Endpoints

### List All Functions

Retrieves a list of all available functions on the server.

- **URL**: `/api/functions`
- **Method**: `GET`
- **Response Format**: JSON object containing a list of function definitions

**Example Response:**
```json
{
  "functions": [
    {
      "name": "calculator", 
      "description": "Performs basic arithmetic operations",
      "parameters": {
        "type": "object",
        "properties": {
          "operation": {
            "type": "string",
            "description": "The operation to perform",
            "enum": ["add", "subtract", "multiply", "divide"]
          },
          "a": {
            "type": "number",
            "description": "First operand"
          },
          "b": {
            "type": "number",
            "description": "Second operand"
          }
        },
        "required": ["operation", "a", "b"]
      }
    }
  ]
}
```

### Get Function Definition

Retrieves the definition of a specific function.

- **URL**: `/api/functions/{name}`
- **Method**: `GET`
- **URL Parameters**: `name` - Name of the function
- **Response Format**: JSON object containing the function definition

**Example Request:**
```
GET /api/functions/calculator
```

**Example Response:**
```json
{
  "name": "calculator", 
  "description": "Performs basic arithmetic operations",
  "parameters": {
    "type": "object",
    "properties": {
      "operation": {
        "type": "string",
        "description": "The operation to perform",
        "enum": ["add", "subtract", "multiply", "divide"]
      },
      "a": {
        "type": "number",
        "description": "First operand"
      },
      "b": {
        "type": "number",
        "description": "Second operand"
      }
    },
    "required": ["operation", "a", "b"]
  }
}
```

### Call Function

Executes a function with the provided parameters.

- **URL**: `/api/functions/call`
- **Method**: `POST`
- **Headers**: `X-API-Key: <your-api-key>`
- **Request Body**: JSON object containing:
  - `name`: Function name
  - `parameters`: Object containing function parameters
- **Response Format**: JSON object containing the function result

**Example Request:**
```json
{
  "name": "calculator",
  "parameters": {
    "operation": "add",
    "a": 5,
    "b": 3
  }
}
```

**Example Response:**
```json
{
  "name": "calculator",
  "result": 8
}
```

### Call Tool

Executes a tool with the provided parameters. Tools extend the function concept with unique identifiers.

- **URL**: `/api/tools/call`
- **Method**: `POST`
- **Headers**: `X-API-Key: <your-api-key>`
- **Request Body**: JSON object containing:
  - `id`: Optional unique identifier for the tool call
  - `function`: Object containing:
    - `name`: Function name
    - `parameters`: Object containing function parameters
- **Response Format**: JSON object containing the tool result

**Example Request:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "function": {
    "name": "calculator",
    "parameters": {
      "operation": "multiply",
      "a": 6,
      "b": 7
    }
  }
}
```

**Example Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "function": {
    "name": "calculator",
    "result": 42
  }
}
```

### Execute from Text

Extracts and executes function calls from natural language text.

- **URL**: `/api/execute`
- **Method**: `POST`
- **Headers**: `X-API-Key: <your-api-key>`
- **Request Body**: JSON object containing:
  - `text`: String containing one or more function calls
- **Response Format**: JSON object or array containing function responses

**Example Request:**
```json
{
  "text": "Calculate 5+3 and transform 'hello' to uppercase."
}
```

**Example Response:**
```json
[
  {
    "name": "calculator",
    "result": 8
  },
  {
    "name": "transform_text",
    "result": "HELLO"
  }
]
```

## WebSocket Endpoints

WebSocket endpoints allow streaming results from function and tool executions.

### Stream Function

Streams the results of a function execution.

- **URL**: `/api/functions/stream`
- **Method**: WebSocket connection
- **Message Format**: JSON object containing:
  - `name`: Function name
  - `parameters`: Object containing function parameters
  - `id`: Optional unique identifier for the call

**Example Message:**
```json
{
  "name": "calculator",
  "parameters": {
    "operation": "add",
    "a": 5,
    "b": 3
  },
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Example Response Chunks:**
```json
{
  "chunk_id": "chunk1",
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "Calculating...",
  "is_final": false,
  "error": null,
  "status": "processing"
}

{
  "chunk_id": "chunk2",
  "call_id": "123e4567-e89b-12d3-a456-426614174000",
  "content": 8,
  "is_final": true,
  "error": null,
  "status": "complete"
}
```

### Stream Tool

Streams the results of a tool execution.

- **URL**: `/api/tools/stream`
- **Method**: WebSocket connection
- **Message Format**: JSON object containing:
  - `id`: Optional unique identifier for the tool call
  - `function`: Object containing:
    - `name`: Function name
    - `parameters`: Object containing function parameters

**Example Message:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "function": {
    "name": "calculator",
    "parameters": {
      "operation": "multiply",
      "a": 6,
      "b": 7
    }
  }
}
```

**Example Response Chunks:**
Same as for the stream function endpoint.

## Client Usage Examples

### Python Client

```python
from mcp_example.adapters.http.client import MCPClient

# Create client
client = MCPClient(
    base_url="http://localhost:8000",
    api_key="test-key"
)

# List available functions
functions = client.list_functions()
for func in functions.functions:
    print(f"{func.name}: {func.description}")

# Call a function
response = client.call_function(
    name="calculator",
    parameters={"operation": "add", "a": 5, "b": 3}
)
print(f"Result: {response.result}")
```

### Asynchronous Streaming Client

```python
import asyncio
from mcp_example.adapters.http.client import AsyncMCPClient

async def main():
    async with AsyncMCPClient(
        base_url="http://localhost:8000",
        api_key="test-key"
    ) as client:
        # Stream function results
        async for chunk in client.stream_function(
            "calculator",
            {"operation": "add", "a": 5, "b": 3}
        ):
            if chunk.error:
                print(f"Error: {chunk.error}")
                break
                
            print(f"Received chunk {chunk.chunk_id}: {chunk.content}")
            
            if chunk.is_final:
                print("Streaming completed.")

if __name__ == "__main__":
    asyncio.run(main())
```

### cURL Examples

List all functions:
```bash
curl -X GET http://localhost:8000/api/functions \
  -H "X-API-Key: test-key"
```

Call a function:
```bash
curl -X POST http://localhost:8000/api/functions/call \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "calculator", "parameters": {"operation": "add", "a": 5, "b": 3}}'
```

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Function or resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a JSON object with `error` and `detail` fields to explain the issue.

**Example Error Response:**
```json
{
  "error": "Function not found",
  "detail": "Function 'unknown_function' not found"
}
```

## Rate Limiting

The server implements basic rate limiting to prevent abuse:
- 100 requests per minute per API key
- WebSocket connections limited to 10 concurrent connections per API key

Exceeding these limits will result in a `429 Too Many Requests` response. 