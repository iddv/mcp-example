"""
Text processing tool for Model Context Protocol.

This module provides text processing tools for text manipulation and analysis.
"""

import re
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition


def transform_text(
    operation: Literal[
        "uppercase", "lowercase", "capitalize", "title", "reverse",
        "count_chars", "count_words", "trim", "replace"
    ],
    text: str,
    find: Optional[str] = None,
    replace_with: Optional[str] = None,
) -> Union[str, int, Dict[str, Any]]:
    """
    Transform text according to the specified operation.

    Args:
        operation: The text operation to perform
        text: The input text
        find: String to find (for replace operation)
        replace_with: String to replace with (for replace operation)

    Returns:
        Transformed text or analysis result

    Raises:
        ValueError: If operation is invalid or missing required parameters
    """
    if not text:
        return ""

    if operation == "uppercase":
        return text.upper()
    
    if operation == "lowercase":
        return text.lower()
    
    if operation == "capitalize":
        return text.capitalize()
    
    if operation == "title":
        return text.title()
    
    if operation == "reverse":
        return text[::-1]
    
    if operation == "count_chars":
        return len(text)
    
    if operation == "count_words":
        return len(text.split())
    
    if operation == "trim":
        return text.strip()
    
    if operation == "replace":
        if find is None:
            raise ValueError("'find' parameter is required for replace operation")
        if replace_with is None:
            replace_with = ""
        return text.replace(find, replace_with)
    
    raise ValueError(f"Unknown operation: {operation}")


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze text and return statistics.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with text statistics
    """
    if not text:
        return {
            "char_count": 0,
            "word_count": 0,
            "line_count": 0,
            "avg_word_length": 0,
            "is_empty": True,
        }
    
    words = re.findall(r'\b\w+\b', text)
    lines = text.split('\n')
    word_count = len(words)
    
    result = {
        "char_count": len(text),
        "word_count": word_count,
        "line_count": len(lines),
        "avg_word_length": sum(len(word) for word in words) / max(1, word_count),
        "is_empty": False,
    }
    
    return result


# Text transform function definition
text_transform_function = FunctionDefinition(
    name="transform_text",
    description="Transform text according to the specified operation",
    parameters={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "The text operation to perform",
                "enum": [
                    "uppercase", "lowercase", "capitalize", "title", "reverse",
                    "count_chars", "count_words", "trim", "replace"
                ],
            },
            "text": {
                "type": "string",
                "description": "The input text",
            },
            "find": {
                "type": "string",
                "description": "String to find (for replace operation)",
            },
            "replace_with": {
                "type": "string",
                "description": "String to replace with (for replace operation)",
            },
        },
        "required": ["operation", "text"],
    },
)

# Text analysis function definition
text_analysis_function = FunctionDefinition(
    name="analyze_text",
    description="Analyze text and return statistics",
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to analyze",
            },
        },
        "required": ["text"],
    },
)


def transform_text_handler(parameters: Dict[str, Any]) -> Union[str, int, Dict[str, Any]]:
    """
    Handler for the transform_text tool that unpacks parameters from a dict.
    
    Args:
        parameters: Dictionary of parameters
        
    Returns:
        Transformed text or analysis result
    """
    return transform_text(
        operation=parameters["operation"],
        text=parameters["text"],
        find=parameters.get("find"),
        replace_with=parameters.get("replace_with")
    )


def analyze_text_handler(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for the analyze_text tool that unpacks parameters from a dict.
    
    Args:
        parameters: Dictionary of parameters
        
    Returns:
        Dictionary with text statistics
    """
    return analyze_text(text=parameters["text"])


def register() -> None:
    """Register the text tools in the global registry."""
    registry.register(text_transform_function, transform_text_handler)
    registry.register(text_analysis_function, analyze_text_handler) 