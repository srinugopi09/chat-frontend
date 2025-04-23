# Logging System Documentation

## Overview

This document describes the production-ready logging system implemented in the Chat App. The logging system is designed to be configurable, secure, and adaptable to different environments while providing comprehensive diagnostic information.

## Table of Contents

1. [Architecture](#architecture)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Sensitive Data Handling](#sensitive-data-handling)
5. [Context Tracking](#context-tracking)
6. [Log Rotation](#log-rotation)
7. [JSON Structured Logging](#json-structured-logging)
8. [Error Handling](#error-handling)
9. [Extending the System](#extending-the-system)

## Architecture

The logging system is built around a singleton `ChatAppLogger` class that wraps Python's built-in logging module with additional functionality:

```
┌────────────────┐     ┌───────────────┐     ┌───────────────────┐
│ Application    │     │ ChatAppLogger │     │ Log Configuration │
│ Components     │────>│ (Singleton)   │<────│ (YAML/ENV)        │
└────────────────┘     └───────┬───────┘     └───────────────────┘
                              │
                      ┌───────┴───────┐
                      ▼               ▼
              ┌───────────────┐ ┌────────────────┐
              │ File Handler  │ │ Console Handler│
              │ (Rotated)     │ │                │
              └───────────────┘ └────────────────┘
```

Key components:

- **ChatAppLogger**: The main logger class that provides enhanced logging capabilities
- **Configuration Layer**: Loads settings from YAML files or environment variables
- **Handlers**: File and console outputs with different formats and levels

## Configuration

### Configuration File

The logging system is configured through a YAML file located at `config/logging.yaml`:

```yaml
# Environment: development, staging, production
environment: development

# Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_level_file: DEBUG
log_level_console: INFO

# Log format: standard or json
log_format: standard

# Log rotation settings
log_retention_days: 30
max_log_size_mb: 10
log_backup_count: 5

# Sensitive fields to mask in logs
sensitive_fields:
  - aws_access_key_id
  - aws_secret_access_key
  - password
  - token
  - auth
  - secret
```

### Environment Variables

You can override any configuration setting with environment variables:

```
CHAT_APP_LOG_ENVIRONMENT=production
CHAT_APP_LOG_LOG_LEVEL_FILE=INFO
CHAT_APP_LOG_LOG_FORMAT=json
```

## Usage

### Initializing the Logger

The logger is typically initialized in the application entry point:

```python
from src.utils.logger import get_logger

config_path = 'config/logging.yaml'
logger = get_logger(config_path)
```

### Using the Logger

Basic logging with different severity levels:

```python
# Simple message logging
logger.debug("Detailed information for debugging purposes")
logger.info("General information about system operation")
logger.warning("Warning about potential issue")
logger.error("Error occurred that affects operation")
logger.critical("Critical error that requires immediate attention")
```

Logging with additional context:

```python
# Add extra context to log messages
logger.info(
    "User performed action", 
    extra={
        "action": "login",
        "user_id": "user123",
        "ip_address": "192.168.1.1"
    }
)
```

### Tracking Request Context

Set request context for correlated logs:

```python
# Generate a request ID
from ulid import ULID
request_id = str(ULID())

# Set request context in logger
logger.set_context(request_id=request_id, user_id=user_id)

# All subsequent logs will include this context automatically
logger.info("Processing request")
```

## Sensitive Data Handling

The logging system automatically masks sensitive data in log messages to prevent exposing credentials or personal information:

```python
# Without masking - DON'T DO THIS
logger.info("Connecting with aws_access_key_id=AKIAIOSFODNN7EXAMPLE")

# With masking (handled automatically)
# Will log: "Connecting with aws_access_key_id=*****"
logger.info("Connecting with aws_access_key_id=AKIAIOSFODNN7EXAMPLE") 
```

Sensitive fields are defined in the configuration and include by default:
- aws_access_key_id
- aws_secret_access_key
- password
- token
- auth
- secret

## Context Tracking

The system tracks the context of operations using:

1. **Request IDs**: A unique ID (ULID) for each request to trace its flow
2. **User IDs**: Associate logs with specific users
3. **Session IDs**: Track logs across user sessions

Example usage:

```python
# Set the context
logger.set_context(request_id="01GMTWH9MYJN7SK8N5AKE14EAM", user_id="user_12345")

# All logs will now include this context
logger.info("User action recorded")
```

## Log Rotation

The system automatically manages log files to prevent disk space issues:

1. **Size-Based Rotation**: Rotates logs when they reach the configured size
2. **Backup Count**: Keeps a fixed number of old log files
3. **Naming Convention**: Uses environment in filenames (e.g., `chat_app_production.log`)

Configuration parameters:
- `max_log_size_mb`: Maximum size before rotation
- `log_backup_count`: Number of backup files to keep

## JSON Structured Logging

For production environments or log processing systems, structured JSON logging is available:

```yaml
# In config/logging.yaml
log_format: json
```

This produces JSON-formatted logs that are easier to parse by log management systems:

```json
{
  "timestamp": "2025-04-21 10:45:22,123",
  "level": "INFO",
  "module": "bedrock",
  "message": "API call completed successfully",
  "request_id": "01GMTWH9MYJN7SK8N5AKE14EAM",
  "user_id": "user_12345",
  "model": "Claude 3.7 V1",
  "response_time": 2.34
}
```

## Error Handling

The logging system includes enhanced error handling:

1. **Categorized Errors**: Different handling based on error types
2. **Structured Error Logs**: Additional context for debugging
3. **Exception Logging**: Full stack traces for critical errors

Example usage:

```python
try:
    # Some operation that might fail
    result = process_data()
except ValidationError as e:
    # Log with specific error type and context
    logger.error(
        f"Data validation error: {str(e)}",
        extra={
            "error_type": "validation",
            "data_id": data_id,
            "field": e.field
        }
    )
except Exception as e:
    # Log unexpected errors with stack trace
    logger.exception(
        f"Unexpected error in data processing: {str(e)}",
        extra={"data_id": data_id}
    )
```

## Extending the System

### Adding New Sensitive Fields

Update the `sensitive_fields` list in the configuration:

```yaml
sensitive_fields:
  - aws_access_key_id
  - aws_secret_access_key
  - password
  - token
  - auth
  - secret
  - credit_card  # New field to mask
```

### Creating Custom Log Handlers

You can extend the `ChatAppLogger` class to add custom handlers:

```python
from src.utils.logger import ChatAppLogger

class EnhancedLogger(ChatAppLogger):
    def __init__(self, config_path):
        super().__init__(config_path)
        self._add_slack_handler()  # Custom handler
        
    def _add_slack_handler(self):
        # Add a handler to send critical errors to Slack
        # ...
```

### Storing Logs in a Database

For applications requiring persistent and queryable logs, implement a database handler:

```python
def _add_db_handler(self):
    from custom_handlers import DatabaseHandler
    db_handler = DatabaseHandler(
        connection_string=self.config.get("db_connection"),
        table_name="application_logs"
    )
    db_handler.setLevel(logging.WARNING)
    self.logger.addHandler(db_handler)
```

## Real-World Examples

### API Request Logging

```python
# Set context for the request
logger.set_context(request_id=str(ULID()), user_id=user.id)

# Log request start with timing
start_time = time.time()
logger.info(f"API request started: {endpoint}", 
           extra={"endpoint": endpoint, "method": request.method})

try:
    # Process the request
    result = process_request(request)
    
    # Log successful completion with timing
    elapsed = time.time() - start_time
    logger.info(
        f"API request completed in {elapsed:.2f}s",
        extra={
            "status_code": 200,
            "response_time": elapsed,
            "endpoint": endpoint
        }
    )
    
    return result
    
except Exception as e:
    # Log failure with context
    elapsed = time.time() - start_time
    logger.exception(
        f"API request failed after {elapsed:.2f}s",
        extra={
            "status_code": 500,
            "endpoint": endpoint,
            "error_type": e.__class__.__name__
        }
    )
    raise
```

### Model Interaction Logging

```python
logger.info(
    f"Invoking model: {model_name}",
    extra={
        "model": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "interaction_type": "model_request"
    }
)

start_time = time.time()
try:
    response = model.generate(prompt, **params)
    
    elapsed = time.time() - start_time
    logger.info(
        f"Model response received in {elapsed:.2f}s",
        extra={
            "model": model_name,
            "response_time": elapsed,
            "token_count": len(response.tokens),
            "interaction_type": "model_response"
        }
    )
    
    return response
    
except ModelError as e:
    elapsed = time.time() - start_time
    logger.error(
        f"Model error after {elapsed:.2f}s: {str(e)}",
        extra={
            "model": model_name,
            "error_type": e.__class__.__name__,
            "interaction_type": "model_error"
        }
    )
    raise
```

## Conclusion

This logging system provides a robust foundation for application monitoring, debugging, and analysis. By following the patterns and practices outlined in this document, you can ensure consistent and useful logs throughout the application.

For any questions or suggestions, please contact the development team.