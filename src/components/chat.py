import streamlit as st
from typing import Dict, Any, List, Optional
import time

from src.utils.message import create_message, is_user_message, is_assistant_message
from src.utils.state_manager import SessionStateManager
from src.connectors.base import BaseLLMConnector
from src.utils.logger import get_logger
from src.utils.config import get_app_config

# Get the logger
logger = get_logger()


def render_message(message: Dict[str, Any]) -> None:
    """
    Render a single message in the chat UI

    Args:
        message: Message dictionary with role, content, and type
    """
    is_user = is_user_message(message)

    # Different styling based on message role
    if is_user:
        avatar = "👤"
        name = "You"
    else:
        avatar = "🤖"
        name = "Assistant"

    with st.chat_message(message["role"], avatar=avatar):
        # Handle different message types
        msg_type = message.get("type", "text")

        # For assistant messages, use collapsible container
        if not is_user and (msg_type == "text" or msg_type == "markdown"):
            with st.expander("Response (click to expand/collapse)", expanded=True):
                st.markdown(message["content"])
        # For user messages and other types, render normally
        elif msg_type == "text" or msg_type == "markdown":
            st.markdown(message["content"])
        elif msg_type == "code":
            st.code(message["content"], language=message.get(
                "metadata", {}).get("language", "python"))
        # Future: Add more renderers for other types


def render_chat_interface(connector: BaseLLMConnector) -> None:
    """
    Render the main chat interface

    Args:
        connector: LLM connector instance
    """
    # Get app configuration
    config = get_app_config()
    
    # Get UI settings
    ui_config = config.ui
    app_title = ui_config.get("title", "AI Chat")
    
    st.title(f"🤖 {app_title}")

    # Initialize state manager
    state_manager = SessionStateManager()
    messages = state_manager.get_messages()

    # Display welcome message if no messages exist
    if not messages:
        st.markdown("""
        ### Welcome to the AI Chat!
        
        Start a conversation with the AI assistant by typing a message below.
        
        Make sure you've set up your AWS credentials in the sidebar.
        """)

    # Display existing messages
    for message in messages:
        render_message(message)

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Skip empty messages
        if prompt.strip():
            # Add user message to state
            user_message = create_message(prompt, role="user", msg_type="text")
            state_manager.add_message(user_message)

            # Display user message
            render_message(user_message)

        # Generate response (with a loading spinner)
        with st.spinner("Thinking..."):
            if connector.is_configured():
                # Get model settings
                model_settings = st.session_state.model_settings if "model_settings" in st.session_state else {}

                # Create a status indicator for the generation process
                status_indicator = st.status(
                    "Generating response...", expanded=True)

                try:
                    # Create placeholder for streaming response
                    with st.chat_message("assistant", avatar="🤖"):
                        # Create the final collapsible container
                        with st.expander("Response (click to expand/collapse)", expanded=True):
                            # Create a placeholder for streaming within the expander
                            response_placeholder = st.empty()
                            full_response = ""

                            # Log request with session context
                            session_id = state_manager.get_session_id()
                            logger.set_context(user_id=session_id)
                            
                            logger.info("Processing user message", 
                                       extra={"interaction_type": "user_message"})
                            
                            messages = state_manager.get_messages()
                            message_count = len(messages)
                            logger.debug(f"Conversation has {message_count} messages")
                            
                            # Log message length statistics
                            if messages and message_count > 0:
                                last_msg_len = len(messages[-1]["content"]) if "content" in messages[-1] else 0
                                logger.debug(f"Latest message length: {last_msg_len} chars")
                            
                            # Stream the response with timing
                            start_time = time.time()
                            chunk_count = 0
                            
                            for chunk in connector.generate_stream(messages, **model_settings):
                                chunk_count += 1
                                full_response += chunk
                                response_placeholder.markdown(full_response + "▌")
                                # Small delay for smoother streaming effect
                                time.sleep(0.01)
                            
                            # Log completion with timing info
                            elapsed_time = time.time() - start_time
                            logger.info(
                                f"Response generated in {elapsed_time:.2f}s with {chunk_count} chunks",
                                extra={
                                    "interaction_type": "model_response",
                                    "response_time": elapsed_time,
                                    "chunk_count": chunk_count,
                                    "model": connector.get_model_name()
                                }
                            )
                            
                            # Final render without cursor
                            response_placeholder.markdown(full_response)

                    # Add assistant response to state
                    assistant_message = create_message(
                        full_response, role="assistant", msg_type="text")
                    state_manager.add_message(assistant_message)

                    # Update status to complete
                    status_indicator.update(
                        label="Response complete!", state="complete")
                except Exception as e:
                    # Create structured error log with context
                    logger.exception(
                        f"Chat interface error: {str(e)}",
                        extra={
                            "error_type": e.__class__.__name__,
                            "user_id": state_manager.get_session_id() if hasattr(state_manager, 'get_session_id') else None,
                            "message_count": len(messages) if 'messages' in locals() else 0
                        }
                    )
                    
                    # Show generic error in UI
                    st.error("An error occurred while processing your request.")
                    
                    # Update status to error
                    status_indicator.update(
                        label="Error occurred", state="error")
                    
                    # Add user-friendly error message to chat history
                    error_message = create_message(
                        "I'm sorry, but I encountered a technical issue. Please try again in a moment or contact support if the problem persists.", 
                        role="assistant", 
                        msg_type="text"
                    )
                    state_manager.add_message(error_message)
            else:
                st.error(
                    "Please configure your AWS credentials in the sidebar to use the chat.")
                # Add error message to chat
                error_message = create_message(
                    "Please configure your AWS credentials in the sidebar to use the chat.",
                    role="assistant",
                    msg_type="text"
                )
                state_manager.add_message(error_message)