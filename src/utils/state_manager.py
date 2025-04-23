import streamlit as st
from typing import List, Dict, Any, Optional

class BaseStateManager:
    """Base class for state management with common interface methods"""
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to history"""
        pass
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Retrieve all messages"""
        pass
    
    def clear_messages(self) -> None:
        """Clear all messages"""
        pass
    
    def get_session_id(self) -> str:
        """Get unique session identifier"""
        pass

class SessionStateManager(BaseStateManager):
    """Implementation using Streamlit's built-in session state"""
    
    def __init__(self):
        self.initialize_session()
    
    def initialize_session(self) -> None:
        """Initialize session state if it doesn't exist"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "session_id" not in st.session_state:
            try:
                # Correct usage for python-ulid package
                from ulid import ULID
                st.session_state.session_id = str(ULID())
            except ImportError:
                # Fallback to UUID if ULID is not available
                import uuid
                st.session_state.session_id = str(uuid.uuid4())
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the session state"""
        st.session_state.messages.append(message)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from the session state"""
        return st.session_state.messages
    
    def clear_messages(self) -> None:
        """Clear all messages from the session state"""
        st.session_state.messages = []
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return st.session_state.session_id