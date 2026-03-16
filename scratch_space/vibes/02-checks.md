# Various checks

## load_env order

if someone depends on fastapi tools, all the variables defined in `~/cred/fastapi-tools/.env` will be loaded.
which might confict with the variables defined in other packages `~/cred/other-package/.env` if they have the same variable names.

eg we might call `load_env` in tests init, so that when running tests we have vars loaded from fastapi tools, but then when running the main app, we have vars loaded from the main app's .env file. ponder on this.

### Analysis

The problem is real. `load_env()` is called at module level in `src/fastapi_tools/__init__.py`:

```python
from fastapi_tools.params.load_env import load_env
load_env()
```

This means the moment any downstream package does `import fastapi_tools` or `from fastapi_tools import create_app`,
it silently loads `~/cred/fastapi-tools/.env` as a side effect. `python-dotenv`'s `load_dotenv`
does NOT override vars already in the environment by default, so load order matters: whichever
`load_env()` runs first wins for any shared variable names.

### Plan

- **Remove the top-level `load_env()` call from `__init__.py`**. A library must not have env-loading
  side effects on import. The function still exists for standalone / dev use.
- For `fastapi-tools`' own tests, add a `tests/conftest.py` that calls `load_env()` explicitly,
  so the test suite still picks up `~/cred/fastapi-tools/.env`.
- Downstream consumers (e.g. `tg-central-hub-bot`) call their own `load_env()` from their own
  params module - that is the correct place to load env vars.
- Document in README: `load_env()` is a convenience helper for running `fastapi-tools` itself;
  do not call it from downstream code.

### Status

- [x] Remove `load_env()` call from `src/fastapi_tools/__init__.py`
- [x] Add `tests/conftest.py` with `load_env()` call
- [x] Add README note under "Setup" clarifying the library vs. app distinction

---

## write notes on local install path in this repo's readme

do it in a clean section
currently no publishing to pypi

### Analysis

The README only shows `uv sync` for installing this package itself. There is no section
explaining how a downstream project adds `fastapi-tools` as a dependency via local path,
which is the only install method until it is published to PyPI.

### Plan

Add a "Using as a dependency" section to README.md with:

```markdown
## Using as a dependency

`fastapi-tools` is not published to PyPI. Install it from a local checkout:

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
```

### Status

- [x] Add "Using as a dependency" section to README.md
