# Backend Architecture

This document explains the organization and structure of the AI Ordering Assistant backend.

## Directory Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration and environment variables
├── cli.py                 # Command-line interface for testing
├── api/
│   ├── __init__.py
│   └── routes.py          # FastAPI route definitions
├── services/
│   ├── __init__.py
│   └── agent.py           # LangChain agent management and order processing
├── schemas/
│   ├── __init__.py
│   └── schemas.py         # Pydantic models for request/response
├── tools/
│   ├── __init__.py
│   └── search_tools.py     # LangChain tools for business/service search
└── tests/
    ├── __init__.py
    └── test_services.py    # Unit tests
```

## Architecture Principles

### 1. Separation of Concerns
- **`main.py`**: Minimal FastAPI app setup and configuration
- **`api/routes.py`**: HTTP endpoint definitions only
- **`services/agent.py`**: Combined agent management and order processing logic
- **`config.py`**: Centralized configuration management
- **`schemas/`**: Data models and validation
- **`tools/`**: LangChain tools and external integrations

### 2. Dependency Flow
```
main.py → api/routes.py → services/agent.py → tools/
                       ↘ schemas/ ↗
```

### 3. Service Layer Pattern
- **AgentService**: Single service that handles both LangChain agent management and order processing
- Service is isolated and can be easily tested/mocked
- Combines related functionality to avoid over-abstraction

### 4. Configuration Management
- All environment variables and settings centralized in `config.py`
- No scattered configuration throughout the codebase
- Easy to modify settings for different environments

## Benefits of This Structure

1. **Testability**: Service can be easily unit tested with mocks
2. **Maintainability**: Clear separation makes code easier to understand and modify
3. **Scalability**: Easy to add new routes or tools
4. **Simplicity**: Avoids unnecessary abstraction layers
5. **Development**: CLI tool separated from web API for easier testing

## Usage

### Running the API
```bash
uvicorn main:app --reload
```

### Running CLI Tests
```bash
python cli.py "I need pizza for 20 people"
```

### Running Unit Tests
```bash
pytest tests/
```

## Adding New Features

1. **New endpoint**: Add to `api/routes.py`
2. **New agent functionality**: Add to `services/agent.py`
3. **New LangChain tool**: Add to `tools/`
4. **New data model**: Add to `schemas/schemas.py`
5. **New configuration**: Add to `config.py` 