# AWS Bedrock Client Implementation

## Overview
This document describes the implementation of the AWS Bedrock client for the Model Context Protocol (MCP) example project. The Bedrock client provides an interface for interacting with language models hosted on AWS Bedrock, including Claude 3.7.

## Implementation Details

### BedrockClientConfig
The `BedrockClientConfig` class defines the configuration options for connecting to AWS Bedrock:

- **region_name**: AWS region where Bedrock is available (default: us-west-2)
- **profile_name**: Optional AWS profile name for authentication
- **access_key_id** and **secret_access_key**: Optional explicit AWS credentials
- **session_token**: Optional session token for temporary credentials
- **max_retries**: Maximum number of retries for failed requests (default: 3)
- **timeout**: Request timeout in seconds (default: 30)
- **endpoint_url**: Optional custom endpoint URL

### BedrockClient
The `BedrockClient` class provides methods for invoking models on AWS Bedrock:

1. **Session and Client Setup**
   - Creates a boto3 session with the provided credentials
   - Initializes a bedrock-runtime client with appropriate configuration

2. **Model Invocation**
   - `invoke_model`: Sends a synchronous request to a Bedrock model
   - `invoke_model_with_response_stream`: Invokes a model with streaming response

3. **Error Handling**
   - Catches and logs boto3 ClientError exceptions
   - Provides detailed error information for debugging

### AsyncBedrockClient
The `AsyncBedrockClient` class provides asynchronous versions of the same functionality:

1. **Asynchronous Bridge**
   - Uses a synchronous BedrockClient internally
   - Runs synchronous operations in separate threads using asyncio.to_thread

2. **Async Methods**
   - `invoke_model`: Asynchronously invokes a Bedrock model
   - `invoke_model_with_response_stream`: Streams model responses asynchronously

## Example Usage

### Synchronous Usage
```python
from mcp_example.adapters.aws.bedrock import BedrockClient, BedrockClientConfig

# Create client with custom configuration
config = BedrockClientConfig(
    region_name="us-east-1",
    profile_name="my-profile",
)
client = BedrockClient(config=config)

# Invoke a model
response = client.invoke_model(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    body={
        "prompt": "Hello, Claude!",
        "max_tokens": 100,
    },
)
print(response)

# Stream response from a model
for chunk in client.invoke_model_with_response_stream(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    body={
        "prompt": "Hello, Claude!",
        "max_tokens": 100,
    },
):
    print(chunk)
```

### Asynchronous Usage
```python
import asyncio
from mcp_example.adapters.aws.bedrock import AsyncBedrockClient, BedrockClientConfig

async def main():
    # Create async client
    client = AsyncBedrockClient()
    
    # Invoke a model asynchronously
    response = await client.invoke_model(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        body={
            "prompt": "Hello, Claude!",
            "max_tokens": 100,
        },
    )
    print(response)
    
    # Stream response asynchronously
    async for chunk in client.invoke_model_with_response_stream(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        body={
            "prompt": "Hello, Claude!",
            "max_tokens": 100,
        },
    ):
        print(chunk)

asyncio.run(main())
```

## Testing
The implementation includes comprehensive unit tests:

1. **Synchronous Client Tests**
   - Tests for client initialization
   - Tests for model invocation
   - Tests for streaming responses

2. **Asynchronous Client Tests**
   - Tests for asynchronous model invocation
   - Tests for asynchronous streaming

The tests use mocking to avoid actual AWS API calls, making them suitable for CI/CD environments.

## Future Improvements
- Add support for model-specific parameter validation
- Implement automatic retries with exponential backoff
- Add support for AWS IAM role-based authentication
- Implement token usage tracking and budgeting
- Add support for Claude 3.7 message history management 