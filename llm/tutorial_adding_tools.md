# Adding New Tools to the MCP Framework

This tutorial guides you through creating and registering new tools in the Model Context Protocol framework. The MCP framework provides a standardized way for language models to invoke functions in your application.

## Overview

A "tool" in MCP consists of:
1. A **function definition** that describes the tool's interface
2. A **handler function** that implements the tool's logic

## Step 1: Create a New Tool File

First, create a new Python file in the `mcp_example/tools/` directory. Name it after your tool, like `weather.py` for a weather tool.

```python
"""
Weather tool for Model Context Protocol.

This module provides a tool for retrieving weather information.
"""

from typing import Dict, Any, Optional
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition
```

## Step 2: Define Your Tool's Main Function

Create a properly typed function with clear docstrings:

```python
def get_weather(location: str, units: Optional[str] = "metric") -> Dict[str, Any]:
    """
    Get current weather for a location.
    
    Args:
        location: City name or coordinates
        units: Temperature units ('metric' or 'imperial')
        
    Returns:
        Weather information including temperature, conditions, etc.
        
    Raises:
        ValueError: If location is invalid or service is unavailable
    """
    # Your weather API implementation goes here
    # For this example, we'll return mock data
    if not location:
        raise ValueError("Location is required")
        
    weather_data = {
        "location": location,
        "temperature": 22.5 if units == "metric" else 72.5,
        "units": "celsius" if units == "metric" else "fahrenheit",
        "conditions": "sunny",
        "humidity": 45,
        "wind_speed": 15,
    }
    
    return weather_data
```

## Step 3: Create a Handler Function

Create a handler that adapts your function for the MCP framework:

```python
def weather_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for the weather tool that unpacks parameters from a dict.
    
    Args:
        parameters: Dictionary of parameters
        
    Returns:
        Weather information 
    """
    return get_weather(
        location=parameters["location"],
        units=parameters.get("units", "metric")
    )
```

## Step 4: Define the Function Schema

Create a function definition that describes the tool's interface:

```python
weather_function = FunctionDefinition(
    name="weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or coordinates",
            },
            "units": {
                "type": "string",
                "description": "Temperature units",
                "enum": ["metric", "imperial"],
                "default": "metric",
            },
        },
        "required": ["location"],
    },
)
```

## Step 5: Create a Register Function

Add a register function that will register your tool in the global registry:

```python
def register() -> None:
    """Register the weather tool in the global registry."""
    registry.register(weather_function, weather_handler)
```

## Step 6: Update the Tools Initialization

Edit `mcp_example/tools/__init__.py` to import and register your new tool:

```python
from . import calculator
from . import text
from . import proxy
from . import weather  # Add this line

def register_all() -> None:
    """Register all available tools."""
    calculator.register()
    text.register()
    proxy.register()
    weather.register()  # Add this line
```

## Step 7: Test Your Tool

You can test your tool through the CLI:

```bash
python -m mcp_example.adapters.stdio.cli
```

Then call your tool:
```
{"name": "weather", "parameters": {"location": "New York", "units": "metric"}}
```

## Advanced: Function Introspection Registration

For simple tools, you can use the registry's introspection capabilities to register directly from a function:

```python
def register_alt() -> None:
    """Alternative registration using introspection."""
    registry.register_from_function(
        get_weather,
        description="Get current weather for a location"
    )
```

## Example: Complete Weather Tool

Here's the complete example of a weather tool:

```python
"""
Weather tool for Model Context Protocol.

This module provides a tool for retrieving weather information.
"""

from typing import Dict, Any, Optional
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition


def get_weather(location: str, units: Optional[str] = "metric") -> Dict[str, Any]:
    """
    Get current weather for a location.
    
    Args:
        location: City name or coordinates
        units: Temperature units ('metric' or 'imperial')
        
    Returns:
        Weather information including temperature, conditions, etc.
        
    Raises:
        ValueError: If location is invalid or service is unavailable
    """
    # Your weather API implementation goes here
    # For this example, we'll return mock data
    if not location:
        raise ValueError("Location is required")
        
    weather_data = {
        "location": location,
        "temperature": 22.5 if units == "metric" else 72.5,
        "units": "celsius" if units == "metric" else "fahrenheit",
        "conditions": "sunny",
        "humidity": 45,
        "wind_speed": 15,
    }
    
    return weather_data


def weather_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for the weather tool that unpacks parameters from a dict.
    
    Args:
        parameters: Dictionary of parameters
        
    Returns:
        Weather information 
    """
    return get_weather(
        location=parameters["location"],
        units=parameters.get("units", "metric")
    )


# Define the function schema
weather_function = FunctionDefinition(
    name="weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or coordinates",
            },
            "units": {
                "type": "string",
                "description": "Temperature units",
                "enum": ["metric", "imperial"],
                "default": "metric",
            },
        },
        "required": ["location"],
    },
)


def register() -> None:
    """Register the weather tool in the global registry."""
    registry.register(weather_function, weather_handler)
```

## Best Practices

1. **Proper Type Hints**: Use Python's type hints to make your functions self-documenting
2. **Comprehensive Documentation**: Write clear docstrings explaining parameters, return values, and exceptions
3. **Input Validation**: Always validate inputs to prevent runtime errors
4. **Error Handling**: Return meaningful error messages for invalid inputs
5. **Parameter Naming**: Use descriptive parameter names that match their purpose
6. **Schema Accuracy**: Ensure your schema accurately reflects the function's capabilities
7. **Testing**: Test your tool both individually and as part of the MCP framework

By following this tutorial, you can create and register new tools in the MCP framework to extend its capabilities for various use cases. 