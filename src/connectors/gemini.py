import json
import boto3
from typing import List, Dict, Any, Optional, Generator
import streamlit as st

from src.connectors.base import BaseLLMConnector
from src.utils.config import get_credentials, get_app_config
from src.utils.message import format_messages_for_bedrock
from src.utils.logger import get_logger

# Get the logger
logger = get_logger()


class BedrockConnector(BaseLLMConnector):
    """Connector for AWS Bedrock"""

    def __init__(self, model_name: str = None):
        """
        Initialize the Bedrock connector.

        Args:
            model_name: The name of the model to use. If None, uses the default from settings.
        """
        config = get_app_config()
        self.model_name = model_name if model_name else config.default_model
        self.bedrock_client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Bedrock client with AWS credentials"""
        try:
            credentials = get_credentials()
            if all(credentials.values()):
                self.bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    aws_access_key_id=credentials.get("aws_access_key_id"),
                    aws_secret_access_key=credentials.get(
                        "aws_secret_access_key"),
                    region_name=credentials.get("region_name")
                )
        except Exception as e:
            st.error(f"Failed to initialize Bedrock client: {str(e)}")
            self.bedrock_client = None

    def is_configured(self) -> bool:
        """Check if the connector is properly configured"""
        return self.bedrock_client is not None

    def get_model_name(self) -> str:
        """Get the current model name"""
        return self.model_name

    def set_model(self, model_name: str) -> None:
        """Set the model to use"""
        self.model_name = model_name

    def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        """Generate a response from Bedrock"""
        if not self.is_configured():
            return "Error: Bedrock is not configured. Please check your AWS credentials."

        try:
            config = get_app_config()
            model_id = config.get_model_id(self.model_name)
            formatted_messages = format_messages_for_bedrock(messages)

            # Prepare the request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get("max_tokens", config.default_model_settings.get("max_tokens", 4096)),
                "temperature": kwargs.get("temperature", config.default_model_settings.get("temperature", 0.7)),
                "top_p": kwargs.get("top_p", config.default_model_settings.get("top_p", 0.9)),
                "top_k": kwargs.get("top_k", config.default_model_settings.get("top_k", 250)),
                "messages": formatted_messages
            }

            # Call Bedrock with the model ID
            logger.debug(f"Using model ID: {model_id}")
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response.get('body').read())
            return response_body.get('content')[0].get('text', '')

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return f"Error: {str(e)}"

    def generate_stream(self, messages: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
        """Generate a streaming response from Bedrock"""
        if not self.is_configured():
            logger.error("Bedrock is not configured. Check AWS credentials.")
            yield "Error: Bedrock is not configured. Please check your AWS credentials."
            return

        try:
            # Log debug info with context
            logger.debug("Starting model request processing")
            
            config = get_app_config()
            model_id = config.get_model_id(self.model_name)
            logger.debug(f"Using model: {self.model_name} (ID: {model_id})")
            
            formatted_messages = format_messages_for_bedrock(messages)
            # Log message count rather than full content for security/privacy
            logger.debug(f"Formatted {len(formatted_messages)} messages for Bedrock")
            
            # Only log detailed message content at trace level in development
            try:
                # Check if logger has config attribute (our custom logger)
                if hasattr(logger, 'config') and logger.config.get("environment") == "development":
                    logger.debug(f"Message content: {json.dumps(formatted_messages, indent=2)}")
            except:
                # Fallback for standard logger
                logger.debug("Message content details omitted (only shown in development mode)")

            # Prepare the request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get("max_tokens", config.default_model_settings.get("max_tokens", 4096)),
                "temperature": kwargs.get("temperature", config.default_model_settings.get("temperature", 0.7)),
                "top_p": kwargs.get("top_p", config.default_model_settings.get("top_p", 0.9)),
                "top_k": kwargs.get("top_k", config.default_model_settings.get("top_k", 250)),
                "messages": formatted_messages
            }
            logger.debug(f"Request prepared with max_tokens={kwargs.get('max_tokens', 4096)}, temperature={kwargs.get('temperature', 0.7)}")

            # Call Bedrock with streaming
            logger.info(f"Invoking Bedrock model: {model_id}")
            response = self.bedrock_client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(request_body)
            )
                
            logger.debug("API call completed successfully")

            stream = response.get('body')
            logger.debug(f"Response stream initialized: {stream is not None}")
            
            if stream:
                logger.debug("Beginning stream processing")
                event_count = 0
                content_chunks = 0
                
                for event in stream:
                    event_count += 1
                    chunk = event.get('chunk')
                    
                    if chunk:
                        try:
                            chunk_data = json.loads(chunk.get('bytes').decode())
                            chunk_type = chunk_data.get('type', '')
                            
                            # Log less verbose information about chunks in production
                            if event_count % 10 == 0 or event_count == 1:
                                logger.debug(f"Processing chunk #{event_count} of type: {chunk_type}")
                            
                            # Handle traditional format with 'content' field
                            if 'content' in chunk_data:
                                if chunk_data['content']:
                                    content = chunk_data['content'][0].get('text', '')
                                    if content:
                                        content_chunks += 1
                                        yield content
                            
                            # Handle new format with 'delta' field (content_block_delta)
                            elif chunk_type == 'content_block_delta' and 'delta' in chunk_data:
                                delta = chunk_data.get('delta', {})
                                if 'text' in delta:
                                    text = delta.get('text', '')
                                    if text:
                                        content_chunks += 1
                                        yield text
                                        
                        except Exception as chunk_error:
                            logger.error(f"Error processing chunk #{event_count}: {str(chunk_error)}")
                
                logger.info(f"Stream complete: processed {event_count} events with {content_chunks} content chunks")

        except Exception as e:
            # Generate a structured error log with context
            error_context = {
                "model": self.model_name,
                "error_type": e.__class__.__name__,
                "message_count": len(messages) if messages else 0
            }
            
            # Log different error levels based on the type of error
            if "ValidationException" in str(e):
                logger.error(
                    f"Bedrock validation error: {str(e)}", 
                    extra={"error_context": error_context}
                )
                # Include more diagnostic info for validation errors
                if formatted_messages and len(formatted_messages) > 0:
                    error_context["first_message_role"] = formatted_messages[0]['role']
                    logger.debug(f"First message role: {formatted_messages[0]['role']}")
                    
                yield "Error: The request format was invalid. This may be due to model requirements or input formatting."
            elif "AccessDenied" in str(e) or "UnrecognizedClient" in str(e):
                logger.error(
                    f"Bedrock authentication error: {str(e)}",
                    extra={"error_context": error_context}
                )
                yield "Error: Unable to authenticate with AWS. Please check your credentials."
            else:
                logger.error(
                    f"Unexpected error in Bedrock request: {str(e)}",
                    extra={"error_context": error_context}
                )
                # Only show generic error to the user
                yield "Error: An unexpected error occurred. Please check logs for details."
                
            # Show error in UI but don't expose details
            st.error("An error occurred while processing your request. Check logs for details.")