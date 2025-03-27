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
        
    # In a real implementation, you'd call a weather API here
    # For example: requests.get(f"https://api.weather.com/current?location={location}")
    
    # Mock data based on the location string
    weather_conditions = {
        "new york": "cloudy",
        "london": "rainy",
        "tokyo": "sunny",
        "sydney": "clear",
        "paris": "partly cloudy",
    }
    
    normalized_location = location.lower()
    condition = weather_conditions.get(normalized_location, "sunny")
    
    # Generate some pseudo-random but consistent values based on location
    # In a real implementation, these would come from an API
    temp_base = sum(ord(c) for c in normalized_location) % 30 + 5  # 5-35°C range
    humidity = (sum(ord(c) for c in normalized_location) % 50) + 30  # 30-80% range
    wind_speed = (sum(ord(c) for c in normalized_location[:3]) % 20) + 5  # 5-25 km/h range
    
    # Convert to imperial if requested
    if units == "imperial":
        temp = temp_base * 9/5 + 32
        temp_unit = "fahrenheit"
        wind_speed = wind_speed * 0.621371  # Convert km/h to mph
        wind_unit = "mph"
    else:
        temp = temp_base
        temp_unit = "celsius"
        wind_unit = "km/h"
    
    weather_data = {
        "location": location,
        "temperature": round(temp, 1),
        "temperature_unit": temp_unit,
        "conditions": condition,
        "humidity": humidity,
        "humidity_unit": "%",
        "wind_speed": round(wind_speed, 1),
        "wind_unit": wind_unit,
        "forecast": "This is a mock weather forecast. In a real implementation, this would provide actual forecast data."
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