# Streamlit Chat Frontend

A reusable and extensible chat application built with Streamlit, designed to work with various LLM frameworks.

## Features

- Clean, modern chat interface
- AWS Bedrock integration (Claude 3.7 and others)
- Centralized configuration system
- Configurable model settings
- Streamlined credential management
- Extensible architecture for adding new LLM connectors
- Component-based UI for easy customization
- Production-ready logging with privacy controls

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/chat-frontend.git
cd chat-frontend
```

2. Install the requirements:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Configuration

The application uses a centralized configuration system:

- Main configuration file: `config/config.yaml`
- Environment variables override (with `CHAT_APP_` prefix)
- AWS credentials can be configured via the UI or environment variables
- Model settings can be configured via the UI or configuration file

You can configure AWS credentials in three ways:
1. Via the application sidebar
2. Using environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`)
3. Creating a `.env` file with the above variables

See the [configuration documentation](docs/configuration.md) for more details.

## Extending the App

### Adding New Renderers

To add support for new message types (charts, tables, etc.), add renderer functions in `src/components/renderers.py`.

### Adding New LLM Connectors

To connect to other frameworks (LangChain, LangGraph, etc.):
1. Create a new connector class in `src/connectors/`
2. Implement the `BaseLLMConnector` interface
3. Update the main app to use your new connector

### Customizing Configuration

To add new configuration sections:
1. Add default values to `AppConfig.DEFAULT_CONFIG` in `src/utils/config.py`
2. Add the values to `config/config.yaml`
3. Optionally add property accessors for easier access

## Documentation

- [Configuration System](docs/configuration.md)
- [Architecture](docs/architecture.md)
- [Logging System](docs/logging.md)
- [Implementation Changes](docs/changes.md)

## License

MIT