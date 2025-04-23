# Chat App Architecture and Data Flow

## Application Startup Flow

When `streamlit run app.py` is executed, the following startup sequence occurs:

```
app.py (Main entry point)
├── Import modules and configure page
├── Initialize components 
│   ├── Render sidebar (src/components/sidebar.py)
│   └── Initialize Bedrock connector (src/connectors/bedrock.py) 
└── Render chat interface (src/components/chat.py)
```

## Detailed Data Flow

### 1. Application Initialization

1. **Entry Point ([`app.py`](../app.py))**:
   - Configures Streamlit page settings
   - Calls [`render_sidebar()`](../src/components/sidebar.py#L6) which returns credentials and model settings
   - Initializes [`BedrockConnector`](../src/connectors/bedrock.py#L8) with the selected model
   - Calls [`render_chat_interface()`](../src/components/chat.py#L36) with the initialized connector

### 2. Configuration Management

1. **Sidebar Rendering ([`src/components/sidebar.py`](../src/components/sidebar.py))**:
   - Loads existing credentials from session state via [`get_credentials()`](../src/utils/config.py#L16)
   - Presents AWS credential input fields
   - Saves credentials to session state via [`save_credentials()`](../src/utils/config.py#L9) when "Save Credentials" is clicked
   - Loads existing model settings via [`get_model_settings()`](../src/utils/config.py#L28)
   - Presents model selection and parameter options
   - Saves model settings to session state via [`save_model_settings()`](../src/utils/config.py#L24) when "Save Settings" is clicked
   - Returns current credentials and model settings

2. **Configuration Management ([`src/utils/config.py`](../src/utils/config.py))**:
   - Manages environment variables
   - Provides functions to save/retrieve credentials from session state
   - Provides functions to save/retrieve model settings from session state
   - Loads default values from environment variables or configuration files

### 3. Chat Interface and State Management

1. **Chat Rendering ([`src/components/chat.py`](../src/components/chat.py))**:
   - Initializes [`SessionStateManager`](../src/utils/state_manager.py#L18) to manage chat history
   - Retrieves existing messages from session state
   - Displays welcome message if no messages exist
   - Renders existing messages using [`render_message()`](../src/components/chat.py#L8)
   - Processes user input when submitted:
     - Creates a message object via [`create_message()`](../src/utils/message.py#L8)
     - Adds message to state via [`state_manager.add_message()`](../src/utils/state_manager.py#L38)
     - Displays the message in UI
     - Generates response using the connector

2. **State Management ([`src/utils/state_manager.py`](../src/utils/state_manager.py))**:
   - [`SessionStateManager`](../src/utils/state_manager.py#L18) implements the [`BaseStateManager`](../src/utils/state_manager.py#L4) interface
   - Initializes session state if it doesn't exist
   - Provides methods to add, retrieve, and clear messages
   - Manages session ID for the current conversation

### 4. Message Processing

1. **Message Utilities ([`src/utils/message.py`](../src/utils/message.py))**:
   - Provides [`create_message()`](../src/utils/message.py#L8) to create standardized message objects
   - Contains helper functions to identify message roles
   - Formats messages for the Bedrock API

2. **Message Rendering ([`src/components/renderers.py`](../src/components/renderers.py))**:
   - Registry of renderer functions for different message types
   - Each renderer knows how to display a specific message type
   - Centralized [`render_message_by_type()`](../src/components/renderers.py#L66) function selects the appropriate renderer

### 5. LLM Integration

1. **Connector Interface ([`src/connectors/base.py`](../src/connectors/base.py))**:
   - Defines the [`BaseLLMConnector`](../src/connectors/base.py#L4) abstract class
   - Specifies methods that all connectors must implement:
     - [`generate_response()`](../src/connectors/base.py#L8) - Generate a complete response
     - [`generate_stream()`](../src/connectors/base.py#L21) - Generate a streaming response
     - [`is_configured()`](../src/connectors/base.py#L34) - Check if properly configured
     - [`get_model_name()`](../src/connectors/base.py#L43) - Get current model name

2. **Bedrock Implementation ([`src/connectors/bedrock.py`](../src/connectors/bedrock.py))**:
   - Implements the `BaseLLMConnector` interface for AWS Bedrock
   - Initializes the Bedrock client with AWS credentials
   - Formats messages for the Claude models
   - Handles both standard and streaming responses
   - Manages error handling and client configuration

3. **Model Configuration ([`src/config/models.py`](../src/config/models.py))**:
   - Contains model IDs for different Bedrock models
   - Provides default model settings
   - Helper functions to get available models and IDs

## Request Flow for a User Message

When a user sends a message, the following sequence occurs:

1. User enters text and clicks send (or presses Enter)
2. Streamlit triggers the `chat_input` callback in [`chat.py`](../src/components/chat.py#L56)
3. A user message object is created via [`create_message()`](../src/utils/message.py#L8)
4. The message is added to session state via [`state_manager.add_message()`](../src/utils/state_manager.py#L38)
5. The message is displayed in the UI
6. The connector is called to generate a response:
   - Credentials and model settings are retrieved from session state
   - Messages are formatted for the Bedrock API
   - The Bedrock client is called with streaming enabled
   - Chunks are streamed back to the UI as they arrive
7. The complete assistant response is added to session state
8. The UI is updated with the complete message

## Component Extensions

### Adding a New Renderer

To add support for a new message type (e.g., chart):

1. Create a new renderer function in [`renderers.py`](../src/components/renderers.py)
2. Register it using the [`@register_renderer`](../src/components/renderers.py#L12) decorator
3. Update the chat component to recognize the new message type

### Adding a New Connector

To integrate a new LLM framework:

1. Create a new connector class that extends [`BaseLLMConnector`](../src/connectors/base.py#L4)
2. Implement all required methods
3. Update the main application to use the new connector

### Extending State Management

To switch to server-side storage:

1. Create a new class that extends [`BaseStateManager`](../src/utils/state_manager.py#L4)
2. Implement all required methods with database operations
3. Update the application to use the new state manager


