# MCP Project Development Guide for LLMs and Agents

## Project Overview
This repository contains a reference implementation of the Model Context Protocol (MCP), which provides standardized ways for LLMs to invoke functions. The overall plan and progress are tracked in `llm/plan.md` and `llm/progress.md`.

## Development Workflow

1. **Check Current Status**: Review `llm/progress.md` to identify the next task to implement
2. **Implement One Task at a Time**: Complete only one task before moving to the next unless changes are tightly coupled
3. **Create Implementation Documentation**: For each completed component, create a new documentation file in the `llm/` directory explaining:
   - Component overview and purpose
   - Implementation details and key design decisions
   - Example usage with code snippets
   - Testing approach
   - Future improvements

4. **Write Tests**: Add unit tests for all new functionality
5. **Update Progress**: Mark completed tasks in `llm/progress.md`
6. **Commit and Push**: Use descriptive commit messages like: `git commit -m "Implement <feature> for Phase X.Y"`

## Project Setup
- First activate the virtual environment with: `source venv/bin/activate` or `source .venv/bin/activate`
- Key directories:
  - `mcp_example/`: Main package containing implementation
  - `tests/`: Unit and integration tests
  - `llm/`: Documentation and planning files

## Testing Guidelines
- Use pytest for all tests
- Mock external dependencies where appropriate
- Test both success and error cases
- For async functions, use pytest-asyncio fixtures

Follow this guide to consistently make progress on the MCP implementation while maintaining code quality and documentation. 