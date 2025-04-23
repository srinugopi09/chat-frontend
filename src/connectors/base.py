from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator

class BaseLLMConnector(ABC):
    """Abstract base class for LLM connectors"""
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate a response from the LLM based on the input messages.
        
        Args:
            messages: List of message objects with role and content
            **kwargs: Additional parameters for the LLM
            
        Returns:
            Response text from the LLM
        """
        pass
    
    @abstractmethod
    def generate_stream(self, messages: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            messages: List of message objects with role and content
            **kwargs: Additional parameters for the LLM
            
        Returns:
            Generator yielding response text chunks
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the connector is properly configured.
        
        Returns:
            True if the connector is configured, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the currently selected model.
        
        Returns:
            Model name
        """
        pass