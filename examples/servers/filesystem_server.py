#!/usr/bin/env python3
"""
Filesystem MCP Server Example

A server that provides safe file system operations:
- Reading files and directories
- File information and metadata
- Text file operations

Run with: mcp dev examples/servers/filesystem_server.py
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import aiofiles
from mcp.server.fastmcp import FastMCP, Context


# Create the MCP server
mcp = FastMCP("Filesystem Server")


# Tools for file operations
@mcp.tool()
async def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Read the contents of a text file.
    
    Args:
        file_path: Path to the file to read
        encoding: Text encoding (default: utf-8)
    """
    try:
        path = Path(file_path).resolve()
        
        # Basic security check - ensure file exists and is readable
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        async with aiofiles.open(path, 'r', encoding=encoding) as f:
            content = await f.read()
        
        return content
    
    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {str(e)}")


@mcp.tool()
def list_directory(dir_path: str, show_hidden: bool = False) -> List[Dict[str, Any]]:
    """
    List contents of a directory.
    
    Args:
        dir_path: Path to the directory
        show_hidden: Whether to show hidden files (starting with .)
    """
    try:
        path = Path(dir_path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        items = []
        for item in path.iterdir():
            # Skip hidden files unless requested
            if not show_hidden and item.name.startswith('.'):
                continue
            
            stat_info = item.stat()
            items.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": stat_info.st_size if item.is_file() else None,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "permissions": stat.filemode(stat_info.st_mode)
            })
        
        # Sort by type (directories first) then by name
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
        return items
    
    except Exception as e:
        raise RuntimeError(f"Error listing directory {dir_path}: {str(e)}")


@mcp.tool()
def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get detailed information about a file or directory.
    
    Args:
        file_path: Path to the file or directory
    """
    try:
        path = Path(file_path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {file_path}")
        
        stat_info = path.stat()
        
        info = {
            "path": str(path),
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": stat_info.st_size,
            "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
            "permissions": stat.filemode(stat_info.st_mode),
            "owner_readable": os.access(path, os.R_OK),
            "owner_writable": os.access(path, os.W_OK),
            "owner_executable": os.access(path, os.X_OK)
        }
        
        if path.is_file():
            info["extension"] = path.suffix
            info["stem"] = path.stem
        
        return info
    
    except Exception as e:
        raise RuntimeError(f"Error getting file info for {file_path}: {str(e)}")


@mcp.tool()
async def search_files(
    directory: str, 
    pattern: str, 
    case_sensitive: bool = False,
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for files matching a pattern in a directory.
    
    Args:
        directory: Directory to search in
        pattern: Filename pattern to search for (supports wildcards)
        case_sensitive: Whether search should be case sensitive
        max_results: Maximum number of results to return
    """
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        # Use glob pattern matching
        if not case_sensitive:
            # For case-insensitive search, we'll need to check manually
            pattern_lower = pattern.lower()
            matches = []
            
            for item in path.rglob("*"):
                if item.is_file() and pattern_lower in item.name.lower():
                    matches.append(item)
                    if len(matches) >= max_results:
                        break
        else:
            matches = list(path.rglob(pattern))[:max_results]
        
        results = []
        for match in matches:
            stat_info = match.stat()
            results.append({
                "path": str(match),
                "name": match.name,
                "size": stat_info.st_size,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "relative_path": str(match.relative_to(path))
            })
        
        return results
    
    except Exception as e:
        raise RuntimeError(f"Error searching files in {directory}: {str(e)}")


# Resources for file system information
@mcp.resource("fs://cwd")
def get_current_directory() -> str:
    """Get the current working directory."""
    return str(Path.cwd())


@mcp.resource("fs://home")
def get_home_directory() -> str:
    """Get the user's home directory."""
    return str(Path.home())


@mcp.resource("fs://info/{path}")
async def get_path_resource(path: str) -> str:
    """Get information about a file system path as a resource."""
    try:
        file_info = get_file_info(path)
        
        info_text = f"""
File System Information for: {path}

Name: {file_info['name']}
Type: {file_info['type']}
Size: {file_info['size']} bytes
Created: {file_info['created']}
Modified: {file_info['modified']}
Permissions: {file_info['permissions']}

Access Rights:
- Readable: {file_info['owner_readable']}
- Writable: {file_info['owner_writable']}
- Executable: {file_info['owner_executable']}
"""
        
        if file_info['type'] == 'file' and file_info.get('extension'):
            info_text += f"\nFile Extension: {file_info['extension']}"
        
        return info_text
    
    except Exception as e:
        return f"Error getting information for {path}: {str(e)}"


# Prompts for file operations
@mcp.prompt()
def file_analysis_prompt(file_path: str) -> str:
    """Generate a prompt for analyzing a file."""
    return f"""
Please analyze the file at: {file_path}

Steps to follow:
1. First, get information about the file using get_file_info
2. If it's a text file, read its contents using read_file
3. Provide a summary including:
   - File type and size
   - Last modification date
   - Content overview (if readable)
   - Any notable patterns or structure

Please be thorough but concise in your analysis.
"""


@mcp.prompt()
def directory_exploration_prompt(directory_path: str) -> str:
    """Generate a prompt for exploring a directory."""
    return f"""
Please explore and summarize the directory: {directory_path}

Steps to follow:
1. List the directory contents using list_directory
2. Identify the types of files and subdirectories
3. Look for any interesting patterns or organization
4. If there are text files, consider reading a few to understand the content
5. Provide a summary of what this directory contains and its apparent purpose

Focus on giving a helpful overview of the directory structure and contents.
"""


if __name__ == "__main__":
    # Run the server
    mcp.run() 