# Fastapi tools

## Installation

### Setup `uv`

To install the package:

Setup [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

### Install the package

Run the following command:

```bash
uv sync --all-extras --all-groups
```

## Docs

Docs are available at [https://pitrified.github.io/fastapi-tools/](https://pitrified.github.io/fastapi-tools/).

## Setup

### Environment Variables

To setup the package, create a `.env` file in `~/cred/fastapi_tools/.env` with the following content:

```bash
FASTAPI_TOOLS_SAMPLE_ENV_VAR=sample
```

`load_env()` (from `fastapi_tools.params.load_env`) is a convenience helper that loads this file.
It is intended for running `fastapi-tools` itself (tests, standalone scripts). Do not call it from
downstream application code - downstream apps should call their own `load_env()` from their own
params module, which loads from their own credentials file.

And for VSCode to recognize the environment file, add the following line to the
workspace [settings file](.vscode/settings.json):

```json
"python.envFile": "/home/pmn/cred/fastapi_tools/.env"
```

Note that the path to the `.env` file should be absolute.

### Pre-commit

To install the pre-commit hooks, run the following command:

```bash
pre-commit install
```

Run against all the files:

```bash
pre-commit run --all-files
```

### Linting

Use pyright for type checking:

```bash
uv run pyright
```

Use ruff for linting:

```bash
uv run ruff check --fix
uv run ruff format
```

### Testing

To run the tests, use the following command:

```bash
uv run pytest
```

or use the VSCode interface.

## Using as a dependency

`fastapi-tools` is not published to PyPI. Install it from a local checkout into a consuming project:

```bash
# from the consuming project root
uv add --editable /path/to/fastapi-tools
```

Or pin it directly in `pyproject.toml`:

```toml
[tool.uv.sources]
fastapi-tools = { path = "../fastapi-tools", editable = true }
```

Then add it to your dependencies:

```toml
[project]
dependencies = ["fastapi-tools"]
```

## IDEAs

- [x] too
- [ ] many
