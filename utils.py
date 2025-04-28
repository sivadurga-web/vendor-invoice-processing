# utils.py
import json
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from termcolor import colored


def load_config_file(filepath: str) -> dict[str, Any]:
    """Load a configuration file.

    Args:
        filepath: Path to the configuration file

    Returns:
        The parsed configuration
    """
    with open(filepath) as f:
        return json.load(f)
    

def extract_relevant_messages(messages: List[Any]) -> List[dict]:
    """
    Extract relevant messages from the interaction, focusing on content and tool calls.
    
    Args:
        messages: List of LangChain message objects (HumanMessage, AIMessage, ToolMessage).
    
    Returns:
        List of cleaned message dictionaries with only relevant information.
    """
    cleaned_messages = []

    for msg in messages:
        cleaned_msg = {"type": msg.__class__.__name__}  # Get the message type (e.g., HumanMessage)

        # Extract content for all message types
        if hasattr(msg, "content") and msg.content:
            cleaned_msg["content"] = msg.content

        # For AIMessage, check if there's a tool call
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            cleaned_msg["tool_calls"] = [
                {
                    "name": tool_call["name"],
                    "args": tool_call["args"]
                }
                for tool_call in msg.tool_calls
            ]

        # For ToolMessage, always include it with its name and content
        if isinstance(msg, ToolMessage):
            cleaned_msg["name"] = msg.name
            if msg.content:  # Ensure content is included even if empty
                cleaned_msg["content"] = msg.content

        # Add the message if it has content, tool calls, or is a ToolMessage
        if "content" in cleaned_msg or "tool_calls" in cleaned_msg or isinstance(msg, ToolMessage):
            cleaned_messages.append(cleaned_msg)

    return cleaned_messages

def pretty_print_response(response: Dict[str, Any], step_name: str) -> None:
    """Pretty print the agent's response to the console with colored sections for agent, tool, and human messages."""
    relevant_messages = extract_relevant_messages(response["messages"])
    
    # Print step header
    print(colored(f"\n{'='*50}", "cyan"))
    print(colored(f"  {step_name}  ", "cyan", attrs=["bold"]))
    print(colored(f"{'='*50}", "cyan"))

    # Group messages by type
    human_messages = [msg for msg in relevant_messages if msg.get("type") == "human"]
    agent_messages = [msg for msg in relevant_messages if msg.get("type") == "agent"]
    tool_messages = [msg for msg in relevant_messages if msg.get("type") == "tool"]

    # Section for Human Messages
    if human_messages:
        print(colored(f"\n{'-'*40}", "yellow"))
        print(colored("HUMAN MESSAGES", "yellow", attrs=["bold"]))
        print(colored(f"{'-'*40}", "yellow"))
        for i, msg in enumerate(human_messages, 1):
            print(colored(f"\n{i}. Human Message:", "yellow"))
            if "content" in msg:
                print(colored(f"   Content: {msg['content']}", "green"))
            if "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    print(colored(f"   Tool Call: {tool_call['name']} with args {tool_call['args']}", "magenta"))
            if "name" in msg:
                print(colored(f"   Name: {msg['name']}", "blue"))

    # Section for Agent Messages
    if agent_messages:
        print(colored(f"\n{'-'*40}", "cyan"))
        print(colored("AGENT MESSAGES", "cyan", attrs=["bold"]))
        print(colored(f"{'-'*40}", "cyan"))
        for i, msg in enumerate(agent_messages, 1):
            print(colored(f"\n{i}. Agent Message:", "cyan"))
            if "content" in msg:
                print(colored(f"   Content: {msg['content']}", "green"))
            if "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    print(colored(f"   Tool Call: {tool_call['name']} with args {tool_call['args']}", "magenta"))
            if "name" in msg:
                print(colored(f"   Name: {msg['name']}", "blue"))

    # Section for Tool Messages
    if tool_messages:
        print(colored(f"\n{'-'*40}", "magenta"))
        print(colored("TOOL MESSAGES", "magenta", attrs=["bold"]))
        print(colored(f"{'-'*40}", "magenta"))
        for i, msg in enumerate(tool_messages, 1):
            print(colored(f"\n{i}. Tool Message:", "magenta"))
            if "content" in msg:
                print(colored(f"   Content: {msg['content']}", "green"))
            if "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    print(colored(f"   Tool Call: {tool_call['name']} with args {tool_call['args']}", "magenta"))
            if "name" in msg:
                print(colored(f"   Name: {msg['name']}", "blue"))

    # Footer
    print(colored(f"\n{'='*50}\n", "cyan"))