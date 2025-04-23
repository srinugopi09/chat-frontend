import os
import yaml
import json
from typing import Dict, Any, Optional, List
from functools import lru_cache
import logging
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class AppConfig:
    """
    Centralized configuration system for the chat application.

    This class manages all application settings from various sources:
    - YAML configuration files
    - Environment variables
    - Default values

    It provides structured access to configuration sections like:
    - Logging configuration
    - Model settings
    - UI configuration
    - etc.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "environment": "development",
        "logging": {
            "level": "INFO",
            "format": "standard",
            "log_level_file": "DEBUG",
            "log_level_console": "INFO",
            "log_retention_days": 30,
            "max_log_size_mb": 10,
            "log_backup_count": 5,
            "sensitive_fields": ["aws_access_key_id", "aws_secret_access_key", "password", "token", "auth", "secret"],
        },
        "models": {
            "default_model": "Claude 3.7 V1",
            "available_models": {
                "Claude 3 Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Claude 3.5 Sonnet V2": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "Claude 3.7 V1": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            },
            "default_settings": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.9,
                "top_k": 250,
            }
        },
        "ui": {
            "title": "AI Chat App",
            "icon": "🤖",
            "layout": "wide",
            "sidebar_state": "expanded",
            "theme": "light"
        },
        "storage": {
            "type": "session",  # session, file, database, redis
            "retention_period_days": 30,
            "max_conversations": 100
        },
        "aws": {
            "region": "us-east-1"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration system.
        
        Args:
            config_path: Optional path to the main configuration file.
                         If not provided, it will look for 'config.yaml' in the config directory.
        """
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Determine config file path
        self.config_path = config_path
        if not self.config_path:
            self.config_path = os.path.join(self.base_path, 'config', 'config.yaml')
            
        # Load configuration
        self.config = self._load_config()
        
        # Initialize logger
        self._logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from files and environment variables"""
        # Start with default configuration
        config = self.DEFAULT_CONFIG.copy()
        
        # Try to load from YAML file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        # Deep merge the configurations
                        self._deep_update(config, file_config)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {str(e)}")
        
        # Try to load legacy configurations
        self._load_legacy_configs(config)
        
        # Override with environment variables
        self._apply_env_overrides(config)
        
        return config
    
    def _load_legacy_configs(self, config: Dict[str, Any]) -> None:
        """Load configurations from legacy files for backward compatibility"""
        # Check for legacy logging.yaml
        logging_path = os.path.join(self.base_path, 'config', 'logging.yaml')
        if os.path.exists(logging_path):
            try:
                with open(logging_path, 'r') as f:
                    logging_config = yaml.safe_load(f)
                    if logging_config:
                        # Update only the logging section
                        self._deep_update(config['logging'], logging_config)
            except Exception as e:
                print(f"Error loading legacy logging config: {str(e)}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides to configuration"""
        # Mapping of environment variable prefixes to config sections
        env_prefixes = {
            "CHAT_APP_LOG_": "logging",
            "CHAT_APP_MODEL_": "models",
            "CHAT_APP_UI_": "ui",
            "CHAT_APP_STORAGE_": "storage",
            "CHAT_APP_AWS_": "aws"
        }
        
        # Process each environment variable
        for env_var, value in os.environ.items():
            # Check if the variable belongs to our application
            for prefix, section in env_prefixes.items():
                if env_var.startswith(prefix):
                    # Extract the key by removing the prefix
                    key = env_var[len(prefix):].lower()
                    
                    # Update the corresponding section
                    if section in config:
                        # Try to convert the value to the appropriate type
                        try:
                            # If original value is a boolean
                            if key in config[section] and isinstance(config[section][key], bool):
                                config[section][key] = value.lower() in ('true', 'yes', '1')
                            # If original value is an integer
                            elif key in config[section] and isinstance(config[section][key], int):
                                config[section][key] = int(value)
                            # If original value is a float
                            elif key in config[section] and isinstance(config[section][key], float):
                                config[section][key] = float(value)
                            # Otherwise, keep as string
                            else:
                                config[section][key] = value
                        except (ValueError, TypeError):
                            config[section][key] = value
            
            # Handle top-level environment variables
            if env_var == "CHAT_APP_ENV":
                config["environment"] = value
            # Handle AWS credentials directly
            elif env_var == "AWS_REGION":
                config["aws"]["region"] = value
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary with another dictionary.
        
        This allows partial updates of nested dictionaries.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    @property
    def environment(self) -> str:
        """Get the current environment"""
        return self.config.get("environment", "development")
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration section"""
        return self.config.get("logging", {})
    
    @property
    def models(self) -> Dict[str, Any]:
        """Get models configuration section"""
        return self.config.get("models", {})
    
    @property
    def available_models(self) -> Dict[str, str]:
        """Get available models dictionary"""
        return self.models.get("available_models", {})
    
    @property
    def model_names(self) -> List[str]:
        """Get list of available model names"""
        return list(self.available_models.keys())
    
    @property
    def default_model(self) -> str:
        """Get default model name"""
        return self.models.get("default_model", "Claude 3.7 V1")
    
    def get_model_id(self, model_name: str) -> str:
        """Get the model ID for a given model name"""
        models = self.available_models
        default = self.default_model
        
        # Return the requested model ID, or the default if not found
        if model_name in models:
            return models[model_name]
        elif default in models:
            return models[default]
        else:
            # Fallback to the first available model
            for name, model_id in models.items():
                return model_id
            
            # If no models are available, return an empty string
            return ""
    
    @property
    def default_model_settings(self) -> Dict[str, Any]:
        """Get default model parameter settings"""
        return self.models.get("default_settings", {})
    
    @property
    def ui(self) -> Dict[str, Any]:
        """Get UI configuration section"""
        return self.config.get("ui", {})
    
    @property
    def aws(self) -> Dict[str, Any]:
        """Get AWS configuration section"""
        return self.config.get("aws", {})
    
    @property
    def storage(self) -> Dict[str, Any]:
        """Get storage configuration section"""
        return self.config.get("storage", {})
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value by section and key.
        
        Args:
            section: Configuration section name
            key: Configuration key within the section
            default: Default value if the key is not found
            
        Returns:
            The configuration value or the default if not found
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"


# Create a singleton instance for global access
@lru_cache(maxsize=1)
def get_app_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Get or create the application configuration.
    
    This function ensures only one configuration instance is created.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        AppConfig instance
    """
    return AppConfig(config_path)


# Legacy functions for backward compatibility

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable or return a default value"""
    return os.environ.get(key, default)

def save_credentials(aws_access_key: str, aws_secret_key: str, region: str) -> None:
    """Save AWS credentials to session state"""
    st.session_state.aws_credentials = {
        "aws_access_key_id": aws_access_key,
        "aws_secret_access_key": aws_secret_key,
        "region_name": region
    }

def get_credentials() -> Dict[str, str]:
    """Get AWS credentials from session state"""
    if "aws_credentials" not in st.session_state:
        # Use environment variables as default
        config = get_app_config()
        st.session_state.aws_credentials = {
            "aws_access_key_id": get_env_var("AWS_ACCESS_KEY_ID", ""),
            "aws_secret_access_key": get_env_var("AWS_SECRET_ACCESS_KEY", ""),
            "region_name": config.aws.get("region", "us-east-1")
        }
    return st.session_state.aws_credentials

def save_model_settings(settings: Dict[str, Any]) -> None:
    """Save model settings to session state"""
    st.session_state.model_settings = settings

def get_model_settings() -> Dict[str, Any]:
    """Get model settings from session state"""
    if "model_settings" not in st.session_state:
        config = get_app_config()
        st.session_state.model_settings = config.default_model_settings.copy()
        st.session_state.model_settings["model"] = config.default_model
    return st.session_state.model_settings