"""
Command-line interface for Model Context Protocol.

This module provides a CLI for interacting with MCP tools via stdio.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from mcp_example.core.executor import ToolExecutor, executor
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionCall, FunctionDefinition, FunctionResponse
from mcp_example.core.validation import extract_function_call_from_text
from mcp_example.tools import register_all_tools

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("mcp.cli")

# Create console for rich output
console = Console()

# Create CLI app
app = typer.Typer(
    help="Model Context Protocol CLI",
    add_completion=False,
)


def print_function_definition(func_def: FunctionDefinition) -> None:
    """
    Print a function definition in a formatted way.

    Args:
        func_def: Function definition to print
    """
    console.print(f"[bold blue]{func_def.name}[/bold blue]")
    console.print(f"  [italic]{func_def.description}[/italic]")
    
    # Create table for parameters
    table = Table(title="Parameters", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Required", style="yellow")
    table.add_column("Description", style="white")
    
    required_params = func_def.parameters.required or []
    
    for name, prop in func_def.parameters.properties.items():
        table.add_row(
            name,
            prop.type,
            "✓" if name in required_params else "",
            prop.description,
        )
    
    console.print(table)
    console.print("")


def print_function_response(response: FunctionResponse) -> None:
    """
    Print a function response in a formatted way.

    Args:
        response: Function response to print
    """
    if response.status == "success":
        console.print("[bold green]Success[/bold green]")
        
        # Format result as JSON if it's a dict
        if isinstance(response.result, dict):
            result_json = json.dumps(response.result, indent=2)
            console.print(Syntax(result_json, "json", theme="monokai"))
        elif isinstance(response.result, list):
            result_json = json.dumps(response.result, indent=2)
            console.print(Syntax(result_json, "json", theme="monokai"))
        else:
            console.print(f"Result: {response.result}")
    else:
        console.print("[bold red]Error[/bold red]")
        console.print(f"Error: {response.error}")


def execute_command(command: str) -> None:
    """
    Execute a command string, which could be a function call or a built-in command.

    Args:
        command: Command string to execute
    """
    # Check for built-in commands
    if command in ("exit", "quit"):
        raise typer.Exit()
    
    if command in ("help", "?"):
        show_help()
        return
    
    if command == "list":
        list_functions()
        return
    
    # Try to parse as a function call
    try:
        # First, check if it's a direct function call format
        if command.startswith("{") and command.endswith("}"):
            try:
                func_call_dict = json.loads(command)
                if "name" in func_call_dict and "parameters" in func_call_dict:
                    func_call = FunctionCall(**func_call_dict)
                    response = executor.execute_function(func_call)
                    print_function_response(response)
                    return
            except json.JSONDecodeError:
                pass
        
        # Try to extract function call from text
        func_call_dict = extract_function_call_from_text(command)
        if func_call_dict:
            func_call = FunctionCall(**func_call_dict)
            response = executor.execute_function(func_call)
            print_function_response(response)
            return
        
        # If we get here, it's not a recognized command or function call
        console.print("[bold red]Error:[/bold red] Unknown command or invalid function call")
        console.print("Type 'help' to see available commands and functions")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


def show_help() -> None:
    """Show help information."""
    console.print(Panel("Model Context Protocol CLI", style="bold blue"))
    console.print("Commands:")
    console.print("  [bold]help[/bold], [bold]?[/bold] - Show this help message")
    console.print("  [bold]list[/bold] - List available functions")
    console.print("  [bold]exit[/bold], [bold]quit[/bold] - Exit the CLI")
    console.print("")
    console.print("Function Call Format:")
    console.print('  {"name": "function_name", "parameters": {"param1": "value1"}}')
    console.print("")
    console.print("Or use natural language to describe the function call.")
    console.print("")


def list_functions() -> None:
    """List all available functions."""
    functions = registry.list_function_definitions()
    
    if not functions:
        console.print("[yellow]No functions registered[/yellow]")
        return
    
    console.print(f"[bold]Available Functions ({len(functions)}):[/bold]")
    for func_def in functions:
        print_function_definition(func_def)


@app.command()
def main() -> None:
    """Start the MCP CLI."""
    # Register all tools
    register_all_tools()
    
    # Show welcome message
    console.print(Panel("Welcome to the Model Context Protocol CLI", style="bold blue"))
    console.print("Type 'help' for available commands or 'list' to see available functions.")
    
    # Start REPL
    while True:
        try:
            command = console.input("\n[bold blue]MCP>[/bold blue] ")
            if command.strip():
                execute_command(command.strip())
        except KeyboardInterrupt:
            console.print("\nUse 'exit' to quit")
        except typer.Exit:
            console.print("\nGoodbye!")
            break
        except Exception as e:
            logger.exception("Error in REPL")
            console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    app() 