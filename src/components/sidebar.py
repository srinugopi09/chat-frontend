import streamlit as st
from typing import Dict, Any, Tuple

from src.utils.config import save_credentials, get_credentials, save_model_settings, get_model_settings, get_app_config


def render_sidebar() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Render the sidebar with configuration options

    Returns:
        Tuple containing (credentials, model_settings)
    """
    # Get app configuration
    config = get_app_config()

    with st.sidebar:
        st.title("🤖 Chat Settings")

        # AWS Credentials section
        st.header("AWS Credentials")

        # Get current credentials
        current_credentials = get_credentials()

        # AWS Credentials input fields
        aws_access_key = st.text_input(
            "AWS Access Key ID",
            value=current_credentials.get("aws_access_key_id", ""),
            type="password"
        )

        aws_secret_key = st.text_input(
            "AWS Secret Access Key",
            value=current_credentials.get("aws_secret_access_key", ""),
            type="password"
        )

        aws_region = st.text_input(
            "AWS Region",
            value=current_credentials.get(
                "region_name", config.aws.get("region", "us-east-1"))
        )

        # Save credentials button
        if st.button("Save Credentials"):
            save_credentials(aws_access_key, aws_secret_key,
                             aws_region)
            st.success("Credentials saved!")

        # Divider
        st.divider()

        # Model settings
        st.header("Model Settings")

        # Get current model settings
        current_settings = get_model_settings()

        # Model selection
        available_models = config.model_names
        default_model = current_settings.get("model", config.default_model)

        # Find index of default model in available models
        default_index = 0
        if default_model in available_models:
            default_index = available_models.index(default_model)

        selected_model = st.selectbox(
            "Model",
            options=available_models,
            index=default_index
        )

        # Model parameters
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=current_settings.get(
                "temperature", config.default_model_settings.get("temperature", 0.7)),
            step=0.01,
            help="Higher values make output more random, lower values more deterministic"
        )

        max_tokens = st.number_input(
            "Max Tokens",
            min_value=1,
            max_value=4096,
            value=current_settings.get(
                "max_tokens", config.default_model_settings.get("max_tokens", 4096)),
            help="Maximum number of tokens to generate"
        )

        # Advanced settings expander
        with st.expander("Advanced Settings"):
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=current_settings.get(
                    "top_p", config.default_model_settings.get("top_p", 0.9)),
                step=0.01,
                help="Nucleus sampling parameter"
            )

            top_k = st.number_input(
                "Top K",
                min_value=0,
                max_value=500,
                value=current_settings.get(
                    "top_k", config.default_model_settings.get("top_k", 250)),
                help="Limits token selection to top K options"
            )

        # Update settings
        new_settings = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "model": selected_model
        }

        # Save settings button
        if st.button("Save Settings"):
            save_model_settings(new_settings)
            st.success("Settings saved!")

        # Divider
        st.divider()

        # Chat controls
        st.header("Chat Controls")

        # Clear chat button
        clear_chat = st.button("Clear Chat History")

        if clear_chat:
            if "messages" in st.session_state:
                st.session_state.messages = []
                st.success("Chat history cleared!")

        # Divider
        st.divider()

        # About section
        st.header("About")
        st.markdown("""
        **Streamlit Chat App**
        
        A modular chat application designed to work with multiple LLM frameworks.
        
        Version: 0.1.0
        """)

    # Return the current settings
    return current_credentials, new_settings
