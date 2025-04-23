import streamlit as st
from typing import Dict, Any, Callable, Dict
import json

# Type for renderer functions
RendererFunc = Callable[[Dict[str, Any], Dict[str, Any]], None]

# Registry of available renderers
RENDERERS: Dict[str, RendererFunc] = {}

def register_renderer(msg_type: str) -> Callable:
    """
    Decorator to register a renderer function for a specific message type
    
    Args:
        msg_type: The message type this renderer handles
        
    Returns:
        Decorator function
    """
    def decorator(func: RendererFunc) -> RendererFunc:
        RENDERERS[msg_type] = func
        return func
    return decorator

@register_renderer("text")
def render_text(message: Dict[str, Any], options: Dict[str, Any]) -> None:
    """Render plain text message"""
    st.write(message["content"])

@register_renderer("markdown")
def render_markdown(message: Dict[str, Any], options: Dict[str, Any]) -> None:
    """Render markdown message"""
    st.markdown(message["content"])

@register_renderer("code")
def render_code(message: Dict[str, Any], options: Dict[str, Any]) -> None:
    """Render code block with syntax highlighting"""
    language = message.get("metadata", {}).get("language", "python")
    st.code(message["content"], language=language)

@register_renderer("json")
def render_json(message: Dict[str, Any], options: Dict[str, Any]) -> None:
    """Render JSON data"""
    try:
        # Parse JSON if it's a string
        if isinstance(message["content"], str):
            data = json.loads(message["content"])
        else:
            data = message["content"]
            
        st.json(data)
    except json.JSONDecodeError:
        st.error("Invalid JSON data")
        st.text(message["content"])

def render_message_by_type(message: Dict[str, Any], options: Dict[str, Any] = None) -> None:
    """
    Render a message based on its type
    
    Args:
        message: The message to render
        options: Optional rendering options
    """
    if options is None:
        options = {}
        
    msg_type = message.get("type", "text")
    
    if msg_type in RENDERERS:
        RENDERERS[msg_type](message, options)
    else:
        # Default to text renderer if type is not supported
        st.write(message["content"])
        st.caption(f"Unhandled message type: {msg_type}")

# Function to create a new renderer
def create_renderer(msg_type: str, renderer_func: RendererFunc) -> None:
    """
    Register a new renderer at runtime
    
    Args:
        msg_type: The message type this renderer handles
        renderer_func: The renderer function
    """
    RENDERERS[msg_type] = renderer_func