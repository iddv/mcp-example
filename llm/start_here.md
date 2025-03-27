# MCP Project Development Guide for LLMs and Agents

## Project Context
This repository contains a reference implementation of the Model Context Protocol (MCP), which provides standardized ways for LLMs to invoke functions. The project follows a phased implementation plan defined in `llm/plan.md`, with progress tracked in `llm/progress.md`.

## How to Work on This Project

### Initial Setup
1. First activate the virtual environment with: `source venv/bin/activate` or `source .venv/bin/activate`
2. Understand the project structure by examining key directories:
   - `mcp_example/`: Main package containing implementation
   - `tests/`: Unit and integration tests
   - `llm/`: Documentation and planning files

### Workflow Process
1. Check `llm/progress.md` to identify the next task to implement
2. Implement only ONE task at a time unless changes are tightly coupled
3. Write unit tests for each new feature
4. Update documentation in `llm/` with implementation details
5. Mark completed tasks in `llm/progress.md`
6. Commit and push changes after each completed task

### Implementation Guidelines
- Follow established code patterns from existing implementation
- Maintain comprehensive test coverage for all new features
- Document each component with docstrings and implementation notes
- Implement the exact requirements specified in the plan without scope creep

## Phase-Specific Instructions

### Core Protocol (Phase 1)
Focus on clean interfaces and robust validation. Ensure schema definitions align with MCP specifications.

### Tools and CLI (Phase 2)
Create intuitive, well-documented tools that follow Unix philosophy of doing one thing well.

### Server Implementation (Phase 3)
Focus on API design, request validation, and proper error handling. Follow RESTful principles.

### Remote Integration (Phase 4)
Ensure robust connection handling with proper retries and error recovery. Document API contracts clearly.

### AWS Bedrock Integration (Phase 5)
Implement secure credential handling and follow AWS best practices. Add thorough error handling for API interactions.

### Documentation (Phase 6)
Focus on clear, example-driven documentation that helps users understand and implement MCP.

## Testing Approach
1. Write unit tests for all new functionality
2. Mock external dependencies (especially AWS services)
3. Ensure both success and error cases are tested
4. For async functions, use pytest-asyncio fixtures and tests

## Documentation Standards
1. Update implementation docs in `llm/` folder for each component
2. Include:
   - Overview of the component
   - Implementation details and key design decisions
   - Example usage with code snippets
   - Testing approach
   - Future improvements

## Commit Process
After completing a task:
1. Run tests to verify functionality: `python -m pytest tests/`
2. Update progress.md to mark task as complete
3. Commit with descriptive message: `git commit -m "Implement <feature> for Phase X.Y"`
4. Push changes: `git push`

Follow this guide to consistently make progress on the MCP implementation while maintaining code quality and documentation standards. 