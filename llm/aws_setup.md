# AWS Bedrock Setup Guide

## Overview
This document provides step-by-step instructions for setting up and configuring AWS Bedrock to work with the Model Context Protocol (MCP) example project. AWS Bedrock is used to access Claude 3.7 and other language models.

## Prerequisites
- An AWS account with Bedrock access
- AWS CLI installed and configured (optional, but recommended)
- Python 3.8 or newer
- MCP example project installed

## Setup Steps

### 1. Enable AWS Bedrock in Your AWS Account

1. Sign in to the AWS Management Console
2. Navigate to the AWS Bedrock service
3. If prompted, click "Get started with AWS Bedrock"
4. In the Bedrock console, navigate to "Model access"
5. Request access to the models you need (e.g., "Anthropic Claude 3.7")
6. Wait for access approval (usually immediate for pay-as-you-go customers)

### 2. Configure AWS Credentials

#### Option A: Using AWS CLI (Recommended)

1. Install the AWS CLI by following instructions at [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. Configure your credentials:
   ```bash
   aws configure
   ```
3. Enter your AWS Access Key ID, Secret Access Key, default region (e.g., us-west-2), and preferred output format (json)

#### Option B: Environment Variables

Set the following environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

#### Option C: Using Credentials in Code

You can provide credentials directly when creating the BedrockClient:
```python
from mcp_example.adapters.aws.bedrock import BedrockClient, BedrockClientConfig

config = BedrockClientConfig(
    region_name="us-west-2",
    access_key_id="your-access-key-id",
    secret_access_key="your-secret-access-key"
)
client = BedrockClient(config=config)
```

### 3. IAM Permissions

Ensure your IAM user or role has the necessary permissions to access Bedrock. Create a policy with:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
```

### 4. Using BedrockClient in Your Application

#### Basic Usage Example

```python
from mcp_example.adapters.aws.bedrock import BedrockClient

# Create client with default configuration (uses AWS CLI credentials)
client = BedrockClient()

# Invoke Claude 3.7 model
response = client.invoke_model(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    body={
        "prompt": "Hello, Claude!",
        "max_tokens": 100,
    },
)
print(response)
```

#### Using Claude 3.7 with the MCP Adapter

```python
from mcp_example.adapters.aws.claude import ClaudeAdapter, ClaudeMessage, ClaudeRole
from mcp_example.core.schema import FunctionDefinition

# Create Claude adapter
adapter = ClaudeAdapter()

# Define messages
messages = [
    ClaudeMessage(role=ClaudeRole.USER, content="What's the weather in Seattle?")
]

# Define function for the model to use
functions = [
    FunctionDefinition(
        name="get_weather",
        description="Get current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    )
]

# Generate a response
response = adapter.generate(messages=messages, functions=functions)
print(response)
```

### 5. Troubleshooting

#### Common Issues and Solutions

1. **AccessDeniedException**:
   - Verify your IAM permissions are correct
   - Check that you've enabled access to the model you're trying to use

2. **ValidationException**:
   - Ensure your request body follows the correct format for the model
   - Check parameter limits (e.g., max_tokens, temperature)

3. **ServiceQuotaExceededException**:
   - Request an increase for your service quotas in the AWS console

4. **Region Availability**:
   - Make sure you're using a region where Bedrock is available
   - As of 2024, Bedrock is available in: us-east-1, us-west-2, and other selected regions

### 6. Cost Management

- Monitor your usage in the AWS Console
- Set up AWS Budgets to receive alerts when costs exceed thresholds
- Consider implementing token counting and budgeting in your application

## References

- [AWS Bedrock Developer Guide](https://docs.aws.amazon.com/bedrock/)
- [Claude 3.7 Documentation](https://docs.anthropic.com/claude/docs)
- [MCP Project Documentation](../README.md)
- [AWS Bedrock Implementation Details](aws_bedrock_implementation.md)
- [Claude Integration Guide](claude_integration.md) 