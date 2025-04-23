from typing import Dict, List, Any

# Bedrock model IDs
BEDROCK_MODELS = {
    "Claude 3 Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "Claude 3.5 Sonnet V2": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "Claude 3.7 V1": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
}

# Default model configurations
DEFAULT_MODEL_SETTINGS = {
    "model": "Claude 3.7 V1",  # Default model to use
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 0.9,
    "top_k": 250,
}


def get_available_models() -> List[str]:
    """Return a list of available model display names"""
    return list(BEDROCK_MODELS.keys())


def get_model_id(model_name: str) -> str:
    """Get the Bedrock model ID for a given display name"""
    default_model = DEFAULT_MODEL_SETTINGS["model"]
    return BEDROCK_MODELS.get(model_name, BEDROCK_MODELS[default_model])


def get_default_settings() -> Dict[str, Any]:
    """Get default model settings"""
    return DEFAULT_MODEL_SETTINGS.copy()
