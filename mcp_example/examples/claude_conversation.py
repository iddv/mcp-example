"""
Claude 3.7 Conversation Flow Example

This script demonstrates how to use Claude 3.7 via AWS Bedrock
with the Model Context Protocol to have a conversation with tool usage.
"""

import asyncio
import logging
from typing import List, Optional

from mcp_example.adapters.aws.claude import AsyncClaudeAdapter, ClaudeConfig, ClaudeMessage, ClaudeRole
from mcp_example.core.registry import registry
from mcp_example.core.schema import FunctionDefinition
from mcp_example.tools import register_all_tools

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def conversation_with_tools(user_messages: List[str], streaming: bool = True) -> None:
    """
    Demonstrate a conversation with Claude 3.7 using tools.
    
    Args:
        user_messages: List of user messages for the conversation
        streaming: Whether to use streaming for responses
    """
    print("=== Claude 3.7 Conversation with Tool Usage ===")
    
    # Register all available tools
    register_all_tools()
    
    # Get tool definitions for Claude
    tool_definitions = registry.get_all_definitions()
    
    # Initialize Claude adapter with default config
    config = ClaudeConfig(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",  # Update to your preferred Claude model
        max_tokens=1024,
        temperature=0.7,
    )
    claude = AsyncClaudeAdapter(config=config)
    
    # Initialize conversation history
    messages = []
    
    # Add system message to explain available tools
    tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in tool_definitions])
    system_message = f"""You are a helpful assistant with access to the following tools:

{tools_description}

Use these tools when needed to provide accurate information and perform tasks.
"""
    
    messages.append(ClaudeMessage(role=ClaudeRole.USER, content=system_message))
    
    # Add initial assistant response
    messages.append(ClaudeMessage(
        role=ClaudeRole.ASSISTANT,
        content="I'm ready to help! I can use various tools like calculator, text processing, and more to assist you."
    ))
    
    # Run the conversation
    for i, user_input in enumerate(user_messages):
        print(f"\nUser: {user_input}")
        
        # Add user message to conversation
        messages.append(ClaudeMessage(role=ClaudeRole.USER, content=user_input))
        
        # Get response from Claude
        if streaming:
            # Using streaming for real-time responses
            print("\nClaude (streaming):", end="", flush=True)
            async for chunk in claude.generate_with_streaming(messages, tool_definitions):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                
                if chunk.function_calls:
                    for call in chunk.function_calls:
                        print(f"\n[Using tool: {call.name}]")
                        print(f"Parameters: {call.parameters}")
                        
                        # Execute the function call
                        from mcp_example.core.executor import executor
                        result = executor.execute_function(call)
                        print(f"Tool result: {result.result}")
                        
                        # Add tool result to conversation
                        tool_message = f"I used the {call.name} tool and got this result: {result.result}"
                        messages.append(ClaudeMessage(role=ClaudeRole.USER, content=tool_message))
            
            print()  # Add a newline after streaming completes
        else:
            # Using non-streaming for simpler implementation
            response = await claude.generate(messages, tool_definitions)
            
            assistant_message = response.get("content", [{"type": "text", "text": "No response"}])
            print("\nClaude:", end=" ")
            
            if isinstance(assistant_message, list):
                for item in assistant_message:
                    if item.get("type") == "text":
                        print(item.get("text", ""))
            else:
                print(assistant_message)
            
            # Check for function calls
            function_calls = claude.extract_function_calls(response)
            
            for call in function_calls:
                print(f"\n[Using tool: {call.name}]")
                print(f"Parameters: {call.parameters}")
                
                # Execute the function call
                from mcp_example.core.executor import executor
                result = executor.execute_function(call)
                print(f"Tool result: {result.result}")
                
                # Add tool result to conversation
                tool_message = f"I used the {call.name} tool and got this result: {result.result}"
                messages.append(ClaudeMessage(role=ClaudeRole.USER, content=tool_message))
            
            # Update conversation with assistant's response
            if function_calls:
                # If there were function calls, get a new response that includes tool results
                follow_up_response = await claude.generate(messages, tool_definitions)
                assistant_content = follow_up_response.get("content", [{"type": "text", "text": "No response"}])
                
                if isinstance(assistant_content, list):
                    assistant_text = ""
                    for item in assistant_content:
                        if item.get("type") == "text":
                            assistant_text += item.get("text", "")
                    
                    print("\nClaude (after using tools):", assistant_text)
                    messages.append(ClaudeMessage(role=ClaudeRole.ASSISTANT, content=assistant_text))
                else:
                    messages.append(ClaudeMessage(role=ClaudeRole.ASSISTANT, content=assistant_content))
            else:
                # No function calls, just add the response to history
                if isinstance(assistant_message, list):
                    assistant_text = ""
                    for item in assistant_message:
                        if item.get("type") == "text":
                            assistant_text += item.get("text", "")
                    messages.append(ClaudeMessage(role=ClaudeRole.ASSISTANT, content=assistant_text))
                else:
                    messages.append(ClaudeMessage(role=ClaudeRole.ASSISTANT, content=assistant_message))


async def main() -> None:
    """Main function to run the example."""
    # Example conversation with tool usage
    user_messages = [
        "What's 42 + 7?",
        "Can you convert 'hello world' to uppercase?",
        "Tell me the result of multiplying 12 by 15, then format it as a dollar amount."
    ]
    
    try:
        await conversation_with_tools(user_messages)
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 