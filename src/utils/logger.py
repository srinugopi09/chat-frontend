import logging
import logging.handlers
import os
import sys
from datetime import datetime
import yaml
import json
from typing import Optional, Dict, Any

class ChatAppLogger:
    """
    Production-ready logging configuration for the chat application.
    
    Features:
    - Environment-based configuration (dev, staging, prod)
    - Log rotation and retention
    - Structured logging (JSON format) option
    - Different log levels for file and console
    - Sensitive data masking
    - Log contexts for request tracking
    """
    
    # Default config values
    DEFAULT_CONFIG = {
        "environment": "development",  # development, staging, production
        "log_level_file": "DEBUG",
        "log_level_console": "INFO",
        "log_format": "standard",  # standard or json
        "log_retention_days": 30,
        "max_log_size_mb": 10,
        "log_backup_count": 5,
        "sensitive_fields": ["aws_access_key_id", "aws_secret_access_key"],
    }
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls, config_path: Optional[str] = None) -> 'ChatAppLogger':
        """Get or create the logger instance"""
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the logger with optional config file"""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Create logs directory if it doesn't exist
        self.logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set up the logger
        self.logger = logging.getLogger('chat_app')
        self.logger.setLevel(logging.DEBUG)  # Base level - handlers will filter
        
        # Clear any existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Add handlers
        self._add_file_handler()
        self._add_console_handler()
        
        # Set global context
        self.request_id = None
        self.user_id = None
        
        # Log startup message
        env = self.config.get("environment", "development")
        self.logger.info(f"Logger initialized in {env} environment")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or environment variables"""
        config = self.DEFAULT_CONFIG.copy()
        
        # Try to load from YAML file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config.update(file_config)
            except Exception as e:
                print(f"Error loading logger config: {str(e)}")
        
        # Override with environment variables if present
        env_prefix = "CHAT_APP_LOG_"
        for key in config.keys():
            env_var = f"{env_prefix}{key.upper()}"
            if env_var in os.environ:
                # Convert string values to appropriate types
                if isinstance(config[key], bool):
                    config[key] = os.environ[env_var].lower() in ('true', 'yes', '1')
                elif isinstance(config[key], int):
                    config[key] = int(os.environ[env_var])
                else:
                    config[key] = os.environ[env_var]
        
        return config
    
    def _add_file_handler(self):
        """Add rotating file handler"""
        log_level = getattr(logging, self.config.get("log_level_file", "DEBUG"))
        max_bytes = self.config.get("max_log_size_mb", 10) * 1024 * 1024
        backup_count = self.config.get("log_backup_count", 5)
        
        # Base log filename includes environment
        env = self.config.get("environment", "development")
        log_file = os.path.join(self.logs_dir, f'chat_app_{env}.log')
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        
        # Set formatter based on config
        if self.config.get("log_format") == "json":
            formatter = self._get_json_formatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _add_console_handler(self):
        """Add console output handler"""
        log_level = getattr(logging, self.config.get("log_level_console", "INFO"))
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Always use simple formatter for console
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _get_json_formatter(self):
        """Create JSON formatter for structured logging"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S,%f")[:-3],
                    "level": record.levelname,
                    "module": record.module,
                    "message": record.getMessage(),
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                
                # Add context attributes if present
                for attr in ["request_id", "user_id", "session_id"]:
                    if hasattr(record, attr):
                        log_data[attr] = getattr(record, attr)
                
                return json.dumps(log_data)
        
        return JsonFormatter()
    
    def _mask_sensitive_data(self, msg: str) -> str:
        """Mask sensitive data in log messages"""
        import re  # Import at function level, not inside the loop
        
        # If message is not a string, convert it
        if not isinstance(msg, str):
            try:
                msg = str(msg)
            except:
                return msg  # Return as is if we can't convert it
                
        masked_msg = msg
        sensitive_fields = self.config.get("sensitive_fields", [])
        
        # Skip masking if there are no sensitive fields or message is empty
        if not sensitive_fields or not masked_msg:
            return masked_msg
            
        # Process each sensitive field
        try:
            for field in sensitive_fields:
                # Simple masking: look for field=value or field: value patterns
                masked_msg = re.sub(
                    fr'{re.escape(field)}[=:]\s*([^\s,"\')]+)', 
                    f'{field}=*****', 
                    masked_msg
                )
                
                # Also look for field in quotes: "field": "value" or 'field': 'value'
                masked_msg = re.sub(
                    fr'["\']?{re.escape(field)}["\']?\s*[=:]\s*["\']([^"\']+)["\']', 
                    f'"{field}": "*****"', 
                    masked_msg
                )
        except Exception as e:
            # Don't let masking errors prevent logging, just note the error
            print(f"Warning: Sensitive data masking error: {str(e)}")
        
        return masked_msg
    
    def set_context(self, request_id: Optional[str] = None, user_id: Optional[str] = None):
        """Set context for the current request/session"""
        self.request_id = request_id
        self.user_id = user_id
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with context"""
        # Add context to extra
        extra = kwargs.pop('extra', {})
        if self.request_id:
            extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
        
        # Mask sensitive data in debug messages
        masked_msg = self._mask_sensitive_data(msg)
        self.logger.debug(masked_msg, *args, extra=extra, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message with context"""
        # Add context to extra
        extra = kwargs.pop('extra', {})
        if self.request_id:
            extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
            
        self.logger.info(msg, *args, extra=extra, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with context"""
        # Add context to extra
        extra = kwargs.pop('extra', {})
        if self.request_id:
            extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
            
        self.logger.warning(msg, *args, extra=extra, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message with context"""
        # Add context to extra
        extra = kwargs.pop('extra', {})
        if self.request_id:
            extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
            
        # Mask sensitive data in error messages
        masked_msg = self._mask_sensitive_data(msg)
        self.logger.error(masked_msg, *args, extra=extra, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with context"""
        # Add context to extra
        extra = kwargs.pop('extra', {})
        if self.request_id:
            extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
            
        # Mask sensitive data in critical messages
        masked_msg = self._mask_sensitive_data(msg)
        self.logger.critical(masked_msg, *args, extra=extra, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with context"""
        # Add context to extra
        extra = kwargs.pop('extra', {})
        if self.request_id:
            extra['request_id'] = self.request_id
        if self.user_id:
            extra['user_id'] = self.user_id
            
        # Mask sensitive data in exception messages
        masked_msg = self._mask_sensitive_data(msg)
        self.logger.exception(masked_msg, *args, extra=extra, **kwargs)


# Helper function to get the logger instance
def get_logger(config_path: Optional[str] = None):
    """Get configured logger instance"""
    return ChatAppLogger.get_instance(config_path)