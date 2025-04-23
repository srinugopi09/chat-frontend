from src.utils.config import get_app_config
from src.components.sidebar import render_sidebar
from src.components.chat import render_chat_interface
from src.connectors.bedrock import BedrockConnector
import streamlit as st
import os
import sys
from typing import Dict, Any, Optional, Tuple

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules


class ChatApplication:
    """
    Main Chat Application class that encapsulates the application's state and behavior.

    This class is responsible for initializing the application, setting up logging,
    managing session state, and rendering the UI components.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Chat Application.

        Args:
            config_path: Optional path to configuration file
        """
        # Load centralized configuration
        self.config = get_app_config(config_path)

        # Configure Streamlit page
        self._configure_page()

        # Set up paths
        self.base_path = os.path.dirname(os.path.abspath(__file__))

        # Initialize components
        self.logger = self._initialize_logger()
        self.request_id = self._generate_request_id()

        if self.logger:
            self.logger.set_context(request_id=self.request_id)
            self.logger.info(
                f"Application initialized with request ID: {self.request_id}")

    def _configure_page(self) -> None:
        """Configure the Streamlit page settings"""
        ui_config = self.config.ui
        st.set_page_config(
            page_title=ui_config.get("title", "AI Chat App"),
            page_icon=ui_config.get("icon", "🤖"),
            layout=ui_config.get("layout", "wide"),
            initial_sidebar_state=ui_config.get("sidebar_state", "expanded")
        )

        # Hide deployment button and other Streamlit UI elements
        self._hide_streamlit_elements()

    def _hide_streamlit_elements(self) -> None:
        """Hide default Streamlit UI elements with custom CSS based on configuration"""
        ui_config = self.config.ui

        # Check configuration to determine what to hide
        hide_menu = ui_config.get("hide_streamlit_menu", True)
        hide_deploy = ui_config.get("hide_deploy_button", True)
        hide_footer = ui_config.get("hide_footer", True)
        custom_styling = ui_config.get("custom_styling", True)
        custom_css = ui_config.get("custom_css", "")

        # Build the CSS based on configuration
        css_parts = []

        if hide_menu:
            css_parts.append(
                "/* Hide hamburger menu */\n#MainMenu {visibility: hidden;}")

        if hide_deploy:
            css_parts.append(
                "/* Hide deploy button */\n.stAppDeployButton {display:none;}")

        if hide_footer:
            css_parts.append(
                "/* Hide 'Made with Streamlit' footer */\nfooter {visibility: hidden;}")

        if custom_styling:
            css_parts.append(
                "/* Additional styling for cleaner look */\n.block-container {padding-top: 1rem; padding-bottom: 1rem;}")
            css_parts.append(
                "/* Custom styling for header */\n.css-18e3th9 {padding-top: 1rem;}")

        # Add any custom CSS from configuration
        if custom_css:
            css_parts.append(
                f"/* Custom CSS from configuration */\n{custom_css}")

        # Only apply CSS if there's something to apply
        if css_parts:
            # Join CSS parts with newlines
            css_content = "\n\n".join(css_parts)

            # Create the style tag with the CSS content
            hide_streamlit_style = f"""
                <style>
                    {css_content}
                </style>
            """
            st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    def _initialize_logger(self):
        """Initialize the logger with configuration"""
        try:
            from src.utils.logger import get_logger
            logging_config_path = os.path.join(
                self.base_path, 'config', 'logging.yaml')
            return get_logger(logging_config_path)
        except Exception as e:
            print(f"Warning: Logger initialization failed: {str(e)}")
            return None

    def _generate_request_id(self) -> str:
        """Generate a unique request ID for this session"""
        try:
            from ulid import ULID
            return str(ULID())
        except ImportError:
            import uuid
            return str(uuid.uuid4())

    def render_sidebar(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Render the sidebar and return the settings"""
        return render_sidebar()

    def initialize_connector(self, model_settings: Dict[str, Any]) -> BedrockConnector:
        """Initialize the LLM connector with the selected model"""
        model_name = model_settings.get("model", self.config.default_model)
        return BedrockConnector(model_name=model_name)

    def render_chat(self, connector: BedrockConnector) -> None:
        """Render the main chat interface"""
        render_chat_interface(connector)

    def run(self) -> None:
        """Run the application"""
        # Render sidebar and get settings
        credentials, model_settings = self.render_sidebar()

        # Initialize the connector
        connector = self.initialize_connector(model_settings)

        # Render chat interface
        self.render_chat(connector)

        # Log successful rendering
        if self.logger:
            self.logger.info("Application UI rendered successfully")


# Entry point
if __name__ == "__main__":
    # Check for config path in command line arguments
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    app = ChatApplication(config_path)
    app.run()
