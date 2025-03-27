"""
AWS adapter package for MCP.
"""

from mcp_example.adapters.aws.bedrock import BedrockClient, AsyncBedrockClient, BedrockClientConfig
from mcp_example.adapters.aws.claude import (
    ClaudeAdapter, 
    AsyncClaudeAdapter, 
    ClaudeConfig, 
    ClaudeMessage, 
    ClaudeRole,
    ClaudeToolChoice
)

__all__ = [
    "BedrockClient",
    "AsyncBedrockClient",
    "BedrockClientConfig",
    "ClaudeAdapter",
    "AsyncClaudeAdapter",
    "ClaudeConfig",
    "ClaudeMessage",
    "ClaudeRole",
    "ClaudeToolChoice"
] 