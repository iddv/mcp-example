# MCP Configuration Examples

This directory contains configuration examples for integrating MCP servers with various clients.

## Claude Desktop Configuration

To use the example servers with Claude Desktop:

1. **Locate your Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the server configurations** from `claude_desktop_config.json` to your config file.

3. **Update the paths** to point to your actual server files:
   ```json
   {
     "mcpServers": {
       "basic-example": {
         "command": "python",
         "args": ["/full/path/to/examples/servers/basic_server.py"],
         "env": {}
       }
     }
   }
   ```

4. **Restart Claude Desktop** to load the new servers.

## Environment Variables

You can pass environment variables to your servers:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_KEY": "your-api-key",
        "DEBUG": "true"
      }
    }
  }
}
```

## Using Virtual Environments

If your servers require specific dependencies, use a virtual environment:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "/path/to/venv/bin/python",
      "args": ["path/to/server.py"],
      "env": {}
    }
  }
}
```

## Testing Configuration

Before adding to Claude Desktop, test your server configuration:

```bash
# Test the server directly
python examples/servers/basic_server.py

# Test with the MCP inspector
mcp dev examples/servers/basic_server.py
```

## Common Issues

1. **Server not starting**: Check that Python path and script path are correct
2. **Import errors**: Ensure all dependencies are installed in the Python environment
3. **Permission errors**: Make sure the script files are executable
4. **Path issues**: Use absolute paths when in doubt

## Advanced Configuration

For more complex setups, you can:

- Use different Python interpreters for different servers
- Set working directories with `cwd` parameter
- Configure timeouts and other transport options
- Use different transports (stdio, HTTP, WebSocket)

See the [MCP documentation](https://modelcontextprotocol.io) for more details. 