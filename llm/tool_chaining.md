# Tool Chaining Implementation

## Overview
This document describes the implementation of tool chaining functionality, which allows for combining local and remote MCP tools in sequence to accomplish more complex tasks. This implementation completes Phase 4.4 of the project plan.

## Implementation Details

### Key Concepts
1. **Tool Chaining**: The process of using the output of one tool as the input to another tool.
2. **Local-Remote Chaining**: Combining tools that are available locally with tools on remote servers.
3. **Proxy-Based Chaining**: Using the proxy tool to access remote tools and then processing the results locally.

### File Structure
- `mcp_example/examples/tool_chaining.py`: Example script demonstrating different approaches to tool chaining.

## Chaining Approaches

### Direct Chaining
Direct chaining involves explicitly passing the result of one tool call as input to another. This approach gives full control over the data flow between tools.

Example:
```python
# Step 1: Call first tool
result1 = executor.execute_function({
    "name": "tool1",
    "parameters": {"param1": "value1"}
})

# Step 2: Use result from first tool as input to second tool
result2 = executor.execute_function({
    "name": "tool2",
    "parameters": {"input": result1.result}
})
```

### Proxy-Based Chaining
Proxy-based chaining uses the proxy tool to access remote servers, then processes the results locally. This approach simplifies access to remote tools.

Example:
```python
# Step 1: Use proxy tool to call remote function
remote_result = executor.execute_function({
    "name": "proxy",
    "parameters": {
        "server_url": "http://example.com",
        "function_name": "remote_tool",
        "parameters": {"param1": "value1"}
    }
})

# Step 2: Process result locally
final_result = executor.execute_function({
    "name": "local_tool",
    "parameters": {"input": remote_result.result}
})
```

### Cross-Server Chaining
Cross-server chaining involves calling tools on different servers in sequence. This approach allows for using specialized tools across a distributed system.

Example:
```python
# Step 1: Call tool on first server
async with AsyncMCPClient("http://server1.com") as client1:
    result1 = await client1.call_function("tool1", {"param1": "value1"})

# Step 2: Send result to second server
async with AsyncMCPClient("http://server2.com") as client2:
    result2 = await client2.call_function("tool2", {"input": result1.result})
```

## Example Implementations

### Local-to-Remote Chaining
The example demonstrates calculating a value locally, then sending it to a remote server for text processing:

1. Use the local calculator tool to add two numbers.
2. Format the result into a message string.
3. Send the message to a remote server for text transformation.

### Proxy Tool Chaining
The example also shows using the proxy tool to:

1. Call a remote calculator to multiply two numbers.
2. Use the result locally with the text processing tool to create a formatted message.

## Benefits of Tool Chaining

1. **Component Reuse**: Each tool can focus on a specific task and be reused in different chains.
2. **Distributed Processing**: Computation can be distributed across multiple servers.
3. **Specialization**: Different servers can specialize in different types of tools.
4. **Flexibility**: Chains can be dynamically constructed based on the task requirements.

## Limitations and Considerations

1. **Error Handling**: Errors in one tool can affect the entire chain.
2. **Performance**: Each link in the chain adds latency.
3. **Data Transformation**: Data formats may need conversion between tools.
4. **Authentication**: Different servers may have different authentication requirements.

## Future Enhancements
Potential improvements for tool chaining include:

1. Declarative chain definitions using a configuration format.
2. Parallel execution of independent chain branches.
3. Conditional branching based on intermediate results.
4. Built-in error recovery and retry mechanisms.
5. Chain visualization and monitoring tools. 