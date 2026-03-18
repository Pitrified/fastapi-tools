# CSS / Static Assets Fix

## Problem

Running `uv run uvicorn project_name.webapp.app:app --reload` from
`python-project-template` serves the app but without any CSS or JS styling.

### Root cause

`templates/base.html` references three vendor assets that do not exist in
`python-project-template/static/`:

| Referenced path | Present? |
|---|---|
| `/static/css/bulma.min.css` | NO |
| `/static/css/app.css` | yes |
| `/static/js/htmx.min.js` | NO |
| `/static/img/logo.svg` | yes |

The factory's debug-docs routes also reference:

| Referenced path | Present? |
|---|---|
| `/static/swagger/swagger-ui-bundle.js` | NO |
| `/static/swagger/swagger-ui.css` | NO |
| `/static/swagger/redoc.standalone.js` | NO |

A `scripts/webapp/cdn_load.sh` script downloads all missing files, but it
requires a manual step and couples projects to specific CDN URLs and versions.
`tg-central-hub-bot` has these files committed to `static/`, confirming they
are required for the app to render correctly.

---

## Fix strategy

Bundle the vendor assets **inside the `fastapi-tools` Python package** and
serve them automatically at `/vendor/`. This eliminates the manual download
step for every project that consumes the library.

### Why `/vendor/` not `/static/`

`create_app()` mounts the project's `static_dir` at `/static/`. Starlette
does not merge two `StaticFiles` mounts at the same prefix, so vendor assets
need their own prefix to avoid conflicts.

---

## Changes

### 1. `fastapi-tools` - add vendor static directory

Create `src/fastapi_tools/_static/` and populate with:

```
src/fastapi_tools/_static/
├── css/
│   └── bulma.min.css      (copy from tg-central-hub-bot/static/css/)
├── js/
│   └── htmx.min.js        (copy from tg-central-hub-bot/static/js/)
└── swagger/
    ├── redoc.standalone.js     (copy from tg-central-hub-bot/static/swagger/)
    ├── swagger-ui-bundle.js    (copy from tg-central-hub-bot/static/swagger/)
    └── swagger-ui.css         (copy from tg-central-hub-bot/static/swagger/)
```

Hatchling includes all non-Python files within the `packages` directory by
default, so no `pyproject.toml` changes are needed.

### 2. `fastapi-tools/src/fastapi_tools/factory.py`

- Define `_VENDOR_STATIC = Path(__file__).parent / "_static"` at module level.
- In `create_app()`, always mount `_VENDOR_STATIC` at `/vendor/`.
- In `_register_docs_routes()`, change swagger/redoc asset URLs from
  `/static/swagger/...` to `/vendor/swagger/...`.

### 3. `python-project-template/templates/base.html`

Update two href/src references:

| Before | After |
|---|---|
| `/static/css/bulma.min.css` | `/vendor/css/bulma.min.css` |
| `/static/js/htmx.min.js` | `/vendor/js/htmx.min.js` |

`/static/css/app.css` and `/static/img/logo.svg` stay unchanged - they are
project-specific assets served from the project's `static_dir`.

### 4. `python-project-template/scripts/webapp/cdn_load.sh`

Remove the Bulma, HTMX, and Swagger/ReDoc download commands (now bundled in
`fastapi-tools`). Keep the directory creation for any future project-specific
assets. Update the echo message accordingly.

---

## Non-changes

- `pyproject.toml` (fastapi-tools) - hatchling already includes non-Python
  files under `packages`; no artifact config needed.
- `tg-central-hub-bot` - out of scope for this fix.
- `configure_templates()` / `make_templates()` - no `/vendor/` template global
  needed; the path is hardcoded in the HTML (same as `/static/`).

---

## Verification

```bash
# fastapi-tools
cd /home/pmn/repos/fastapi-tools
uv run pytest && uv run ruff check . && uv run pyright

# python-project-template
cd /home/pmn/repos/python-project-template
uv run pytest && uv run ruff check . && uv run pyright
```

Then run the dev server and confirm CSS renders:
```bash
cd /home/pmn/repos/python-project-template
uv run uvicorn project_name.webapp.app:app --reload
# visit http://127.0.0.1:8000 - Bulma navy header and styled cards should appear
```
