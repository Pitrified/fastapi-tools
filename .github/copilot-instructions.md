# fastapi-tools - Copilot Instructions

## Project overview

`fastapi-tools` is ...

## Running & tooling

```bash
uv run pytest                        # run tests
uv run ruff check .                  # lint (ruff, ALL rules enabled)
uv run pyright                       # type-check (src/ and tests/ only)

uv run mkdocs serve                  # MkDocs local docs server
```

Credentials live at `~/cred/fastapi-tools/.env` (loaded by `load_env()` in `src/fastapi-tools/params/load_env.py`).

## Architecture layers

...

## Key patterns

**`Fastapi-toolsParams` singleton**  
Access project-wide config via `get_fastapi-tools_params()` from `src/fastapi-tools/params/fastapi-tools_params.py`. It aggregates `Fastapi-toolsPaths`, `SampleParams`, and `WebappParams`. Environment is controlled by `ENV_STAGE_TYPE` (`dev`/`prod`) and `ENV_LOCATION_TYPE` (`local`/`render`) env vars.

```python
from fastapi-tools.params.fastapi-tools_params import get_fastapi-tools_params

params = get_fastapi-tools_params()
paths = params.paths          # Fastapi-toolsPaths
webapp = params.webapp        # WebappParams
```

**`BaseModelKwargs`**  
Extend `BaseModelKwargs` (not plain `BaseModel`) for any config that needs to be forwarded as `**kwargs` to a third-party constructor. `to_kw(exclude_none=True)` flattens a nested `kwargs` dict at the top level.

```python
class SampleConfig(BaseModelKwargs):
    some_int: int
    nested_model: NestedModel
    kwargs: dict = Field(default_factory=dict)

cfg = SampleConfig(some_int=1, nested_model=NestedModel(some_str="hi"), kwargs={"extra": True})
cfg.to_kw(exclude_none=True)  # {"some_int": 1, "nested_model": ..., "extra": True}
```

**Config / Params separation**

- `src/fastapi-tools/config/` holds Pydantic models that define the _shape_ of settings.
- `src/fastapi-tools/params/` holds plain classes that load _actual values_ (from env vars, `.env` file, etc.) and instantiate config models.
- Never read env vars directly in config models; do it in the corresponding `Params` class.

## Style rules

- Never use em dashes (`--` or `---` or Unicode `—`). Use a hyphen `-` or rewrite the sentence.
- Use `loguru` (`from loguru import logger as lg`) for all logging.
- Raise descriptive custom exceptions (e.g., `UnknownEnvLocationError`) rather than bare `ValueError`/`RuntimeError`.

## Testing & scratch space

- Tests live in `tests/` mirroring `src/fastapi-tools/` structure.
- `scratch_space/` holds numbered exploratory notebooks and scripts. Not part of the package; ruff ignores `ERA001`/`F401`/`T20` there.

## Linting notes

- `ruff.toml` targets Python 3.14 with `select = ["ALL"]`. Key ignores: `COM812`, `D104`, `D203`, `D213`, `D413`, `FIX002`, `RET504`, `TD002`, `TD003`.
- Tests additionally allow `ARG001`, `INP001`, `PLR2004`, `S101`.
- Notebooks (`*.ipynb`) additionally allow `ERA001`, `F401`, `T20`.
- `meta/*` additionally allows `INP001`, `T20`.
- `max-args = 10` (pylint).

## End-of-task verification

After every code change, run the full verification suite before considering the task done:

```bash
uv run pytest && uv run ruff check . && uv run pyright
```
