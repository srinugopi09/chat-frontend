from typing import Dict, Any, Literal, Optional
import time

MessageRole = Literal["user", "assistant", "system"]
MessageType = Literal["text", "code", "markdown", "chart", "form", "table"]

def create_message(
    content: str, 
    role: MessageRole = "user", 
    msg_type: MessageType = "text",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized message object for the chat application.
    
    Args:
        content: The message content
        role: The sender role (user, assistant, system)
        msg_type: The message content type for rendering purposes
        metadata: Optional metadata for specialized message types
    
    Returns:
        A message dictionary with consistent structure
    """
    return {
        "content": content,
        "role": role,
        "type": msg_type,
        "metadata": metadata or {},
        "timestamp": time.time()
    }

def is_user_message(message: Dict[str, Any]) -> bool:
    """Check if a message is from the user"""
    return message.get("role") == "user"

def is_assistant_message(message: Dict[str, Any]) -> bool:
    """Check if a message is from the assistant"""
    return message.get("role") == "assistant"

def is_system_message(message: Dict[str, Any]) -> bool:
    """Check if a message is a system message"""
    return message.get("role") == "system"

def format_messages_for_bedrock(messages: list) -> list:
    """
    Format messages for Bedrock's Claude model.
    
    Args:
        messages: List of message objects
        
    Returns:
        List formatted for Claude models
    """
    formatted_messages = []
    
    for msg in messages:
        # Skip empty messages
        if not msg.get("content", "").strip():
            continue
            
        formatted_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Bedrock requires at least one message
    if not formatted_messages:
        formatted_messages.append({
            "role": "user",
            "content": "Hello"
        })
        
    return formatted_messages