# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=examples

# Code formatting and linting
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run mypy .
```

### MCP Server Operations
```bash
# Test server with MCP inspector (development mode)
mcp dev examples/servers/basic_server.py
mcp dev examples/servers/filesystem_server.py

# Run servers directly
python examples/servers/basic_server.py
python examples/servers/filesystem_server.py

# Run client examples
python examples/clients/basic_client.py

# Install server for Claude Desktop
mcp install examples/servers/basic_server.py
```

## Architecture

This repository demonstrates Model Context Protocol (MCP) implementations with a clear client-server architecture:

### Core Components
- **Servers** (`examples/servers/`): Expose tools, resources, and prompts via MCP
- **Clients** (`examples/clients/`): Connect to and interact with MCP servers
- **Configs** (`examples/configs/`): Configuration examples for Claude Desktop integration

### MCP Server Pattern
All servers use the FastMCP framework and follow this pattern:
- `@mcp.tool()` - Functions the LLM can execute
- `@mcp.resource()` - Data the LLM can access (URI-based)
- `@mcp.prompt()` - Templates for LLM interactions
- `mcp.run()` - Starts the stdio transport server

### Transport Layer
- Primary transport: stdio (for Claude Desktop integration)
- Servers communicate via JSON-RPC over stdin/stdout
- Client sessions handle connection initialization and message exchange

### Example Servers
- **basic_server.py**: Mathematical tools, server info resources, helper prompts
- **filesystem_server.py**: File system operations with security constraints, path-based resources

### Security Model
- File operations validate paths and check permissions
- Input validation in all tools to prevent malicious usage
- Error handling that doesn't expose sensitive information
- Path resolution prevents directory traversal attacks

## Key Patterns

### Resource URI Schemes
- `info://` - Server information and metadata
- `config://` - Configuration and capabilities
- `examples://` - Usage examples and documentation
- `fs://` - File system resources (filesystem server)

### Error Handling
All tools wrap operations in try-catch blocks and raise RuntimeError with descriptive messages rather than exposing raw exceptions.

### Async Operations
File I/O operations use `aiofiles` for async file reading, while synchronous operations are used for metadata and directory listings.