# Configuration System Documentation

## Overview

The chat application uses a centralized configuration system that provides a unified approach to managing settings across the application. This document explains how the configuration system works, where settings are stored, and how to customize them.

## Architecture

The configuration system follows a layered approach with multiple sources of configuration:

1. **Default Values**: Hardcoded defaults in the `AppConfig` class
2. **YAML Configuration**: Settings stored in `config/config.yaml`
3. **Legacy Configurations**: Backward compatibility with existing config files
4. **Environment Variables**: Overrides via environment variables
5. **Session State**: Runtime configuration stored in Streamlit's session state

These sources are applied in the order listed above, with later sources overriding earlier ones.

## Main Configuration File

The main configuration file is located at `config/config.yaml`. It contains settings organized into sections:

```yaml
# Environment: development, staging, production
environment: development

# UI configuration
ui:
  title: "AI Chat App"
  icon: "🤖"
  layout: "wide"
  sidebar_state: "expanded"
  theme: "light"

# AWS configuration
aws:
  region: "us-east-1"

# Model configuration
models:
  default_model: "Claude 3.7 V1"
  available_models:
    "Claude 3 Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0"
    "Claude 3.5 Sonnet V2": "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    "Claude 3.7 V1": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  default_settings:
    temperature: 0.7
    max_tokens: 4096
    top_p: 0.9
    top_k: 250

# Storage configuration
storage:
  type: "session"
  retention_period_days: 30
  max_conversations: 100

# Logging configuration
logging:
  level: "INFO"
  format: "standard"
```

## Configuration API

The configuration is accessed through the `AppConfig` class, which provides a clean API for retrieving settings.

### Basic Usage

```python
from src.utils.config import get_app_config

# Get the configuration singleton
config = get_app_config()

# Access configuration values
environment = config.environment
aws_region = config.aws.get("region")
default_model = config.default_model
```

### Property Accessors

The `AppConfig` class provides convenient property accessors for common configuration sections:

- `config.environment`: Current environment (development, staging, production)
- `config.logging`: Logging configuration
- `config.models`: Model configuration
- `config.available_models`: Dictionary of available model names and IDs
- `config.model_names`: List of available model names
- `config.default_model`: Default model name
- `config.default_model_settings`: Default model parameters
- `config.ui`: UI configuration
- `config.aws`: AWS configuration
- `config.storage`: Storage configuration

### Helper Methods

Additional helper methods are available:

- `config.get_model_id(model_name)`: Get the model ID for a given model name
- `config.get(section, key, default)`: Get a specific configuration value
- `config.is_development()`: Check if in development environment
- `config.is_production()`: Check if in production environment

### Legacy Functions

For backward compatibility, the following functions are still available:

- `get_env_var(key, default)`: Get an environment variable
- `save_credentials(aws_access_key, aws_secret_key, region, inference_profile_arn)`: Save AWS credentials
- `get_credentials()`: Get AWS credentials
- `save_model_settings(settings)`: Save model settings
- `get_model_settings()`: Get model settings

## Environment Variables

You can override any configuration setting using environment variables. The environment variables follow a specific naming pattern:

- Top-level environment: `CHAT_APP_ENV`
- AWS region: `AWS_REGION`
- Section-specific: `CHAT_APP_<SECTION>_<KEY>`

Examples:
- `CHAT_APP_ENV=production` - Set the environment to production
- `CHAT_APP_LOG_LEVEL=DEBUG` - Set the log level to DEBUG
- `CHAT_APP_MODEL_DEFAULT_MODEL="Claude 3.5 Sonnet V2"` - Change the default model
- `CHAT_APP_UI_THEME=dark` - Change the UI theme

## Adding New Configuration Sections

To add a new configuration section:

1. Add the default values to the `DEFAULT_CONFIG` dictionary in `AppConfig`
2. Add them to the `config.yaml` file
3. Add the prefix mapping in the `_apply_env_overrides` method if needed
4. Optionally add property accessors for easier access

## Runtime Configuration

Some settings, like AWS credentials and model settings, are stored in Streamlit's session state and can be changed at runtime through the UI. These settings take precedence over the file-based configuration.

## Security Considerations

Sensitive information like API keys and credentials should be provided through environment variables, not in the configuration files. The configuration system automatically masks sensitive values in logs.