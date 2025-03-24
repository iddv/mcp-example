"""
Calculator tool for Model Context Protocol.

This module provides a calculator tool for performing basic arithmetic operations.
"""

import math
import operator
from typing import Any, Dict, List, Literal, Optional, Union

from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition, PropertySchema


def calculate(
    operation: Literal["add", "subtract", "multiply", "divide", "power", "sqrt", "log"],
    a: float,
    b: Optional[float] = None,
) -> float:
    """
    Perform a basic arithmetic calculation.

    Args:
        operation: The operation to perform
        a: First operand
        b: Second operand (required for all operations except sqrt)

    Returns:
        Result of the operation

    Raises:
        ValueError: If operation is invalid or division by zero
    """
    print(f"Calculator called with operation={operation}, a={a}, b={b}")
    operations = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "divide": operator.truediv,
        "power": math.pow,
    }

    if operation in operations:
        if b is None:
            raise ValueError(f"Second operand is required for operation '{operation}'")
        
        if operation == "divide" and b == 0:
            raise ValueError("Division by zero is not allowed")
        
        return operations[operation](a, b)
    
    if operation == "sqrt":
        if a < 0:
            raise ValueError("Cannot calculate square root of a negative number")
        return math.sqrt(a)
    
    if operation == "log":
        if a <= 0:
            raise ValueError("Cannot calculate logarithm of a non-positive number")
        
        if b is None or b <= 0:
            raise ValueError("Base must be a positive number")
        
        return math.log(a, b)
    
    raise ValueError(f"Unknown operation: {operation}")


def calculate_handler(parameters: Dict[str, Any]) -> float:
    """
    Handler for the calculator tool that unpacks parameters from a dict.
    
    Args:
        parameters: Dictionary of parameters
        
    Returns:
        Result of the calculation
    """
    return calculate(
        operation=parameters["operation"],
        a=parameters["a"],
        b=parameters.get("b")
    )


# Register the calculator tool
calculator_function = FunctionDefinition(
    name="calculator",
    description="Perform basic arithmetic calculations",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "The operation to perform",
                "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt", "log"],
            },
            "a": {
                "type": "number",
                "description": "First operand",
            },
            "b": {
                "type": "number",
                "description": "Second operand (required for all operations except sqrt)",
            },
        },
        "required": ["operation", "a"],
    },
)


def register() -> None:
    """Register the calculator tool in the global registry."""
    registry.register(calculator_function, calculate_handler) 