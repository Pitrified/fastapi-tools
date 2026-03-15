# Fastapi Tools

Welcome to the **Fastapi Tools** documentation.

This is a Python project template designed to help you quickly bootstrap new Python projects with best practices baked in.

## Features

- **Modern Python**: Built for Python 3.13+
- **Dependency Management**: Uses [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management
- **Code Quality**: Pre-configured with Ruff, Pyright, and pre-commit hooks
- **Testing**: Pytest setup with sensible defaults
- **Documentation**: MkDocs with Material theme and auto-generated API docs

## Quick Start

```bash
# Clone the template
git clone https://github.com/YOUR_USERNAME/fastapi-tools.git
cd fastapi-tools

# Install dependencies
uv sync

# Run tests
uv run pytest

# Start documentation server
uv sync --group docs
uv run mkdocs serve
```

## Project Structure

```
fastapi-tools/
├── src/fastapi_tools/     # Main application code
│   ├── config/           # Configuration management
│   ├── data_models/      # Pydantic models
│   ├── metaclasses/      # Custom metaclasses
│   └── params/           # Parameters and paths
├── tests/                # Test suite
├── docs/                 # Documentation (you are here)
├── scratch_space/        # Experimental notebooks
└── meta/                 # Project renaming utilities
```

## Next Steps

- [Getting Started](getting-started.md) - Set up your development environment
- [Guides](guides/uv.md) - Learn about the tools used in this project
- [API Reference](reference/) - Explore the codebase
- [Contributing](contributing.md) - How to contribute to this project
