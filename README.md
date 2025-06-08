# 🎯 MCP Examples - Enterprise Edition

> **🚀 FastMCP 2.0 powered examples for building sophisticated Model Context Protocol servers**

Welcome to the ultimate MCP examples repository! Build enterprise-grade AI servers with our **living Minesweeper example** and comprehensive FastMCP 2.0 templates.

[![FastMCP](https://img.shields.io/badge/FastMCP-2.7.1-blue?style=for-the-badge)](https://github.com/jlowin/fastmcp)
[![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple?style=for-the-badge)](https://modelcontextprotocol.io)

## ✨ What's New in This Edition

🎮 **Living Game Example**: Watch LLMs master Minesweeper through logical reasoning  
🚀 **FastMCP 2.0**: Enterprise features with multiple transport protocols  
🏢 **Production Ready**: Authentication, sessions, real-time data, WebSocket support  
🤖 **AI Agent Friendly**: Complete templates and guides for automated server generation  

## 🎯 Featured: Minesweeper MCP Server

**The ultimate demonstration of AI logical reasoning!**

```bash
# Start the Minesweeper server
mcp dev examples/servers/minesweeper_server.py

# Or run as HTTP server
python examples/servers/minesweeper_server.py --transport http --port 8000
```

**Watch an LLM play Minesweeper:**
```python
# Start a new expert game
new_game("expert")  # 30x16 grid, 99 mines!

# Get AI-powered strategic hints  
get_hint(game_id)   # Returns probability analysis

# Make strategic moves
reveal(game_id, x, y)  # Uncover cells
flag(game_id, x, y)    # Mark mines

# Analyze the board
analyze_board(game_id)  # Full probability matrix
```

![Minesweeper Demo](https://img.shields.io/badge/🎮-Interactive_Demo-brightgreen?style=for-the-badge)

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (FastMCP 2.0 requirement)
- **Poetry** (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-examples.git
cd mcp-examples

# Install with Poetry (recommended)
poetry install

# Or with pip
pip install -e .
```

### 🎮 Try the Minesweeper Server

```bash
# Development mode with MCP inspector
mcp dev examples/servers/minesweeper_server.py

# HTTP server for web integration
python examples/servers/minesweeper_server.py --transport http --port 8000

# Test with the basic client
python examples/clients/basic_client.py
```

## 📁 Project Structure

```
examples/
├── servers/
│   ├── basic_server.py          # Simple MCP server (official SDK)
│   ├── filesystem_server.py     # File operations server
│   ├── minesweeper_server.py    # 🎯 Ultimate game server (FastMCP 2.0)
│   └── comprehensive_server.py  # Full feature showcase
├── clients/
│   └── basic_client.py          # MCP client examples
└── configs/
    ├── claude_desktop_config.json
    └── README.md

# Documentation
├── FASTMCP_AI_AGENT_GUIDE.md    # Complete FastMCP 2.0 guide
├── AI_AGENT_INSTRUCTIONS.md     # Instructions for AI agents
└── CLAUDE.md                    # Project guidelines
```

## 🎮 Minesweeper Server Features

### 🧠 AI-Powered Gameplay
- **Strategic Tools**: `new_game()`, `reveal()`, `flag()`, `get_hint()`
- **Analysis Tools**: `analyze_board()`, probability calculations
- **Learning Resources**: Strategy guides, pattern libraries, tutorials

### 🏢 Enterprise Features
- **Multiple Transports**: stdio, HTTP, WebSocket ready
- **Session Management**: Multiple concurrent games
- **Real-time Updates**: Live game state streaming
- **Authentication Ready**: OAuth 2.0 support built-in
- **Statistics**: Global leaderboards and analytics

### 📚 Educational Resources
- **Strategy Guide**: Master-level Minesweeper techniques
- **Pattern Library**: Common configurations and solutions
- **AI Prompts**: Teaching assistant for learning players
- **Probability Analysis**: Mathematical approach to decision making

## 🔧 Server Examples

### 🎯 Minesweeper (FastMCP 2.0)
```python
from fastmcp import FastMCP

mcp = FastMCP("🎯 Minesweeper Pro")

@mcp.tool
def new_game(difficulty: str = "beginner") -> dict:
    """🎮 Start a new Minesweeper game!"""
    game_id = game_engine.create_game(difficulty)
    return {"game_id": game_id, "message": "Good luck! 🎯"}

@mcp.resource("game://state/{game_id}")
def get_game_state(game_id: str) -> str:
    """Real-time game state resource."""
    return format_game_display(game_id)

@mcp.prompt
def strategy_guide(situation: str) -> str:
    """Generate strategic analysis for current situation."""
    return f"Strategic guidance for: {situation}..."
```

### 🔧 Basic Server (Official SDK)
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Basic Example Server")

@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@mcp.resource("info://server")
def get_server_info() -> str:
    """Server information resource."""
    return "Basic MCP Server Example..."
```

## 🤖 For AI Agents

**This repository is optimized for AI agents to build MCP servers!**

### 📖 Complete Guides
- **[FastMCP 2.0 AI Agent Guide](FASTMCP_AI_AGENT_GUIDE.md)** - Enterprise server building
- **[AI Agent Instructions](AI_AGENT_INSTRUCTIONS.md)** - Step-by-step templates
- **Live Examples** - Copy and modify working servers

### 🎯 Use Cases
- **Game Servers**: Interactive entertainment with real-time state
- **Data Processing**: Complex analysis with streaming results  
- **API Integration**: External service coordination
- **Educational Tools**: Interactive learning systems
- **Productivity Apps**: Task management and automation

## 🏢 Enterprise Features (FastMCP 2.0)

### 🚀 Multiple Transports
```python
# Development: stdio (default)
mcp.run()

# Production: HTTP with streaming
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

# WebSocket support ready
mcp.run(transport="websocket", host="127.0.0.1", port=8080)
```

### 🔐 Authentication & Security
```python
@mcp.set_auth_config
def auth_config():
    return {
        "authorization_url": "https://your-auth.com/oauth/authorize",
        "token_url": "https://your-auth.com/oauth/token",
        "client_id": os.getenv("CLIENT_ID"),
        "scopes": ["read", "write", "admin"]
    }
```

### 📊 Real-time Data & Sessions
```python
@mcp.tool
async def create_session(user_id: str, data: dict) -> dict:
    """Create stateful user sessions."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"user": user_id, "data": data}
    return {"session_id": session_id}

@mcp.resource("stream://live-data")
async def live_data() -> str:
    """Streaming real-time data."""
    return f"Live update: {time.time()}"
```

## 🔧 Development Commands

```bash
# Development & Testing
mcp dev examples/servers/minesweeper_server.py
mcp dev examples/servers/basic_server.py

# HTTP Servers
python examples/servers/minesweeper_server.py --transport http --port 8000
python examples/servers/comprehensive_server.py --http --port 8080

# Install for Claude Desktop
mcp install examples/servers/minesweeper_server.py

# Run tests
poetry run pytest
poetry run pytest --cov=examples

# Code quality
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run mypy .
```

## 🎯 Claude Desktop Integration

1. **Copy configuration** from `examples/configs/claude_desktop_config.json`
2. **Update server paths** to match your setup:

```json
{
  "mcpServers": {
    "minesweeper": {
      "command": "python",
      "args": ["/path/to/examples/servers/minesweeper_server.py"]
    },
    "filesystem": {
      "command": "python", 
      "args": ["/path/to/examples/servers/filesystem_server.py"]
    }
  }
}
```

3. **Restart Claude Desktop** and start playing! 🎮

## 🎮 Minesweeper Gameplay Examples

### 🎯 Start Playing
```python
# Create a new game
result = new_game("intermediate")  # 16x16, 40 mines
game_id = result["game_id"]

# Make your first move
reveal(game_id, 8, 8)  # Start in the center

# Get strategic advice
hint = get_hint(game_id)
# Returns: {"action": "reveal", "x": 5, "y": 3, "reason": "0% mine probability"}
```

### 🧮 Advanced Analysis
```python
# Full probability analysis
analysis = analyze_board(game_id)
# Returns probability matrix for all hidden cells

# Strategic guidance
prompt = analyze_strategy(game_id, "stuck on complex constraint")
# Returns step-by-step strategic guidance
```

### 📊 Statistics & Learning
```python
# Check your progress
stats = list_games()
# Shows win rate, best times, active games

# Learn from the masters
guide = get_strategy_guide()
# Comprehensive strategy documentation
```

## 🧪 Testing Your Servers

### 🔍 MCP Inspector
```bash
# Test any server interactively
mcp dev examples/servers/minesweeper_server.py
mcp dev examples/servers/basic_server.py
```

### 🤖 Programmatic Testing
```python
# Test with FastMCP's built-in testing
from fastmcp.testing import create_test_client

async def test_minesweeper():
    client = create_test_client(mcp)
    
    # Test game creation
    result = await client.call_tool("new_game", {"difficulty": "beginner"})
    assert result["success"] == True
    
    # Test resources
    info = await client.get_resource("stats://global")
    assert "Statistics" in info
```

## 🌟 What Makes This Special

### 🎮 Living Examples
- **Interactive Gameplay**: Watch LLMs learn and strategize
- **Real-time State**: See decision-making processes unfold
- **Educational Value**: Understand AI reasoning through play

### 🏢 Enterprise Ready
- **Production Deployment**: HTTP servers, authentication, sessions
- **Scalable Architecture**: Multiple transports, WebSocket support  
- **Monitoring & Analytics**: Built-in statistics and performance tracking

### 🤖 AI Agent Optimized
- **Complete Templates**: Copy-paste server generators
- **Comprehensive Docs**: Everything needed for autonomous building
- **Best Practices**: Security, error handling, testing patterns

## 📚 Learn More

- **[FastMCP Documentation](https://gofastmcp.com)** - Official FastMCP 2.0 docs
- **[MCP Specification](https://spec.modelcontextprotocol.io)** - Protocol specification  
- **[Official MCP SDK](https://github.com/modelcontextprotocol/python-sdk)** - Python SDK
- **[MCP Community](https://github.com/modelcontextprotocol)** - Community resources

## 🤝 Contributing

We welcome contributions! Whether it's:

- 🎮 **New game examples** (Chess, Tic-tac-toe, Sudoku)
- 🏢 **Enterprise patterns** (Authentication, monitoring, deployment)
- 🤖 **AI agent tools** (Templates, generators, testing)
- 📚 **Documentation** (Tutorials, guides, examples)

### Guidelines
- Keep examples **practical and educational**
- Include **comprehensive documentation**  
- Follow **security best practices**
- Add **proper error handling**
- Use **type hints** throughout

## 🏆 Showcase

**Built something cool with these examples?** We'd love to feature it!

- Enterprise MCP deployments
- Educational AI systems  
- Interactive game servers
- Creative LLM applications

## 📄 License

MIT License - build whatever you want! See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **[Anthropic](https://anthropic.com)** - For creating MCP and making AI better
- **[Jeremiah Lowin](https://github.com/jlowin)** - For the amazing FastMCP framework
- **[MCP Community](https://github.com/modelcontextprotocol)** - For the excellent ecosystem
- **Contributors** - Who make this repository awesome

---

## 🎯 Ready to Build?

```bash
# Start with Minesweeper
mcp dev examples/servers/minesweeper_server.py

# Read the AI agent guide
cat FASTMCP_AI_AGENT_GUIDE.md

# Build your own server
cp examples/servers/minesweeper_server.py my_server.py
```

**🚀 Happy building! Let's make MCP servers that are both powerful and fun!** 🎮