# MCP Project Development Guide

## Overview
This repository implements the Model Context Protocol (MCP), providing standardized ways for LLMs to invoke functions. Progress is tracked in `llm/progress.md`.

## Development Workflow

1. **Check Current Status**: Review `llm/progress.md` to identify the next task
2. **Study Existing Code First**: Before implementing, study the actual interfaces, models, and patterns used in related components
3. **Verify Assumptions**: Double-check method names, field names, and expected behavior against the actual codebase
4. **Test Before Committing**: Run tests to verify your implementation works correctly
5. **Document Your Work**: Create documentation in the `llm/` directory for completed components

## Key Project Structure
- `mcp_example/`: Main implementation package
- `tests/`: Unit and integration tests
- `llm/`: Documentation and planning files

## Testing
- Use pytest: `python -m pytest tests/path/to/test_file.py -v`
- Test both success and error cases

Following this guide will help maintain code quality and avoid common implementation mistakes like incorrect method names, invalid field access, or mismatched interfaces. 