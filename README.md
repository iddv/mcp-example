# Model Context Protocol (MCP) Example

A reference implementation of the Model Context Protocol (MCP) for tool calling between LLMs and applications.

## Overview

This project serves as both a client and server implementation of the Model Context Protocol. It demonstrates:
- Local tool calling via stdio
- Remote tool calling via HTTP
- Integration with AWS Bedrock and Claude 3.7

The Model Context Protocol facilitates interaction between LLMs and tools or applications by defining standard formats for function definitions, function calls, and responses.

## AI-Assisted Development

This project was created with the assistance of Claude 3.7, Anthropic's advanced AI assistant. The planning, implementation strategy, and technical decisions are documented in the `llm/` directory, which contains:
- Design specifications
- Implementation plans
- Technical decisions
- Development progress

These documents provide insight into the AI-assisted development process and can serve as a reference for similar projects.

## Project Structure

```
mcp-example/
├── core/                 # Core protocol implementation
│   ├── schema.py         # Protocol schema definitions
│   ├── validation.py     # Schema validation utilities
│   ├── registry.py       # Tool registry
│   └── executor.py       # Tool executor
├── tools/                # Tool implementations
│   ├── calculator.py     # Calculator tool
│   └── text.py           # Text processing tool
├── adapters/             # Interface adapters
│   ├── stdio/            # Command-line interface
│   └── http/             # HTTP client for remote servers
├── server/               # Server implementation
│   ├── app.py            # FastAPI server
│   └── main.py           # Server runner
├── examples/             # Usage examples
├── tests/                # Test suite
└── llm/                  # Implementation documentation
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mcp-example.git
   cd mcp-example
   ```

2. Set up a virtual environment and install dependencies:

   Option 1: Using Poetry (recommended):
   ```
   poetry install
   ```

   Option 2: Using venv:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   pip install -e .
   ```

### Running the CLI

The command-line interface provides a way to interact with tools locally:

```
# With Poetry
poetry run python -m mcp_example.adapters.stdio.cli

# With venv
python -m mcp_example.adapters.stdio.cli
```

This will start a REPL where you can:
- List available tools with the `list` command
- Call tools directly with JSON syntax: `{"name": "calculator", "parameters": {"operation": "add", "a": 5, "b": 3}}`
- Get help with the `help` command

### Running the Server

The FastAPI server provides a remote API for tool calling:

```
# With Poetry
poetry run python -m mcp_example.server.main --host 0.0.0.0 --port 8000

# With venv
python -m mcp_example.server.main --host 0.0.0.0 --port 8000
```

By default, this starts a server on `http://127.0.0.1:8000`. You can access API documentation at `http://127.0.0.1:8000/docs`.

Server options:
- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to listen on (default: 8000)
- `--reload`: Enable auto-reload for development
- `--log-level`: Set logging level (debug, info, warning, error)

### Testing the Server

Once the server is running, you can test it using curl:

1. List available functions:
   ```
   curl -X GET http://localhost:8000/api/functions -H "X-API-Key: test-key"
   ```

2. Call the calculator function:
   ```
   curl -X POST http://localhost:8000/api/functions/call \
     -H "X-API-Key: test-key" \
     -H "Content-Type: application/json" \
     -d '{"name": "calculator", "parameters": {"operation": "add", "a": 5, "b": 3}}'
   ```

3. Transform text to uppercase:
   ```
   curl -X POST http://localhost:8000/api/functions/call \
     -H "X-API-Key: test-key" \
     -H "Content-Type: application/json" \
     -d '{"name": "transform_text", "parameters": {"operation": "uppercase", "text": "hello world"}}'
   ```

4. Analyze text:
   ```
   curl -X POST http://localhost:8000/api/functions/call \
     -H "X-API-Key: test-key" \
     -H "Content-Type: application/json" \
     -d '{"name": "analyze_text", "parameters": {"text": "Hello world. This is a test."}}'
   ```

### Troubleshooting

If you encounter any issues:

1. Make sure all dependencies are installed:
   ```
   pip list | grep uvicorn  # Should show uvicorn is installed
   ```

2. Check for circular import errors in the logs:
   ```
   python -m mcp_example.server.main --log-level debug
   ```

3. Verify the API key is included in your requests (default is "test-key")

### API Endpoints

The server provides the following endpoints:

- `GET /api/functions`: List all available functions
- `GET /api/functions/{name}`: Get a specific function definition
- `POST /api/functions/call`: Call a function
- `POST /api/tools/call`: Call a tool
- `POST /api/execute`: Execute a function call from text

### Using the HTTP Client

To call the server from a Python application:

```python
from mcp_example.adapters.http.client import MCPClient

# Create client
client = MCPClient(
    base_url="http://localhost:8000",
    api_key="test-key"  # Use the default test key
)

# List available functions
functions = client.list_functions()
for func in functions:
    print(f"{func.name}: {func.description}")

# Call a function
response = client.call_function(
    name="calculator",
    parameters={"operation": "add", "a": 5, "b": 3}
)
print(f"Result: {response.result}")
```

## Available Tools

### Calculator

Performs basic arithmetic operations:
- add: Addition (a + b)
- subtract: Subtraction (a - b)
- multiply: Multiplication (a * b)
- divide: Division (a / b)
- power: Exponentiation (a ^ b)
- sqrt: Square root (√a)
- log: Logarithm (log_b(a))

### Text Processing

Provides text transformation and analysis:

Transform operations:
- uppercase: Convert text to uppercase
- lowercase: Convert text to lowercase
- capitalize: Capitalize first letter
- title: Convert to title case
- reverse: Reverse text
- count_chars: Count characters
- count_words: Count words
- trim: Remove leading/trailing whitespace
- replace: Replace text

Text analysis:
- Provides statistics about text (character count, word count, etc.)

## Documentation

Detailed documentation is available in the `llm/` directory:
- `plan.md`: Implementation plan
- `progress.md`: Current implementation status
- `decisions.md`: Key design decisions
- `challenges.md`: Implementation challenges and solutions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 