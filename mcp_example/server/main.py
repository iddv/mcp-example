"""
Main script to run the MCP FastAPI server.
"""

import logging
import os
import sys
import uvicorn
from typing import Dict, List, Optional

import typer

from mcp_example.server.app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp.server")

# Create CLI app
cli = typer.Typer(
    help="MCP Server CLI",
    add_completion=False,
)


@cli.command()
def start(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind the server to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind the server to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    log_level: str = typer.Option(
        "info", "--log-level", "-l", help="Logging level (debug, info, warning, error)"
    ),
) -> None:
    """Start the MCP server."""
    # Map log level string to logging level
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    
    # Set log level
    logging.getLogger().setLevel(log_levels.get(log_level.lower(), logging.INFO))
    
    logger.info(f"Starting MCP server on {host}:{port}")
    logger.info(f"Log level: {log_level}")
    
    # Start server
    uvicorn.run(
        "mcp_example.server.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    cli() 