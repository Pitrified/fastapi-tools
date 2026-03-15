# `fastapi-tools` — Implementation Plan

> **Scope**: Extract the reusable FastAPI scaffold from `python-project-template`
> (main branch) and `tg-central-hub-bot` (feat-sample_app_flow branch) into a
> standalone installable library. Update the copier template to consume it.
> Do **not** touch the Telegram repo yet.

---

## 1. New repo: `fastapi-tools`

### 1.1 Repo bootstrap (DONE)

- Create `Pitrified/fastapi-tools` on GitHub (public)
- Bootstrap with `python-project-template` copier (use itself once copier is wired, or manually for now): uv, ruff, pre-commit, mkdocs, `.python-version = 3.14`
- Package name: `fastapi-tools`
- `src/fastapi_tools/` layout

### 1.2 Dependencies (`pyproject.toml`)

```toml
[project]
name = "fastapi-tools"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",   # ProxyHeadersMiddleware lives here
    "python-multipart>=0.0.6",
    "itsdangerous>=2.1.0",
    "httpx>=0.26.0",
    "email-validator>=2.3.0",
    "jinja2>=3.1.0",
    "loguru>=0.7.3",
    "pydantic>=2.0",
    "starlette>=0.36.0",           # transitive via fastapi, pinned for middleware types
]
```

---

## 2. File-by-file migration

For each file: source → destination, and any changes required.

### 2.1 `src/fastapi_tools/config.py`

**Sources**:
- `src/project_name/config/webapp/webapp_config.py` (template)
- `src/tg_central_hub_bot/config/webapp/webapp_config.py` (TG — adds `trusted_hosts`, `public_base_url`)

**Action**: Merge both. TG version is the superset — use it verbatim, replace
`tg_central_hub_bot` import with `fastapi_tools`.

**Result — classes exported**:
- `CORSConfig`
- `SessionConfig`
- `RateLimitConfig`
- `GoogleOAuthConfig`
- `WebappConfig` — includes `trusted_hosts: list[str]` and `public_base_url: str | None`

**Change**: Replace `from tg_central_hub_bot.data_models.basemodel_kwargs import BaseModelKwargs`
with `from fastapi_tools.models.base import BaseModelKwargs`.

---

### 2.2 `src/fastapi_tools/models/base.py`

**Source**: `src/project_name/data_models/basemodel_kwargs.py`

**Action**: Copy verbatim, no import changes needed (no internal deps).

**Exports**: `BaseModelKwargs`

---

### 2.3 `src/fastapi_tools/utils/singleton.py`

**Source**: `src/project_name/metaclasses/singleton.py`

**Action**: Copy verbatim.

**Exports**: `Singleton`

---

### 2.4 `src/fastapi_tools/utils/url.py`

**Source**: `src/tg_central_hub_bot/webapp/utils/url_utils.py` (TG only — not in template)

**Action**: Copy verbatim, no import changes (no internal deps).

**Exports**: `get_public_base_url(request, override)`

---

### 2.5 `src/fastapi_tools/security.py`

**Source**: `src/project_name/webapp/core/security.py`

**Action**: Copy verbatim, no import changes.

**Exports**: `TokenManager`, `generate_session_id`, `generate_state_token`,
`hash_token`, `sanitize_html`, `sanitize_dict`, `get_expiration_time`, `is_expired`

---

### 2.6 `src/fastapi_tools/exceptions.py`

**Source**: `src/project_name/webapp/core/exceptions.py`

**Action**: Copy verbatim, no import changes.

**Exports**: `NotAuthenticatedException`, `NotAuthorizedException`,
`RateLimitExceededException`, `ValidationException`, `ServiceUnavailableException`

---

### 2.7 `src/fastapi_tools/middleware.py`

**Source**: `src/project_name/webapp/core/middleware.py`

**Action**: Copy verbatim. Replace import:
```python
# before
from project_name.config.webapp import WebappConfig
# after
from fastapi_tools.config import WebappConfig
```

**Exports**: `RequestIDMiddleware`, `SecurityHeadersMiddleware`,
`RequestLoggingMiddleware`, `setup_middleware(app, config)`

---

### 2.8 `src/fastapi_tools/schemas/auth.py`

**Source**: `src/project_name/webapp/schemas/auth_schemas.py`

**Action**: Copy verbatim. Replace import:
```python
# before
from project_name.data_models.basemodel_kwargs import BaseModelKwargs
# after
from fastapi_tools.models.base import BaseModelKwargs
```

**Exports**: `SessionData`, `UserResponse`, `GoogleUserInfo`, `AuthURLResponse`,
`LogoutResponse`

---

### 2.9 `src/fastapi_tools/schemas/common.py`

**Source**: `src/project_name/webapp/schemas/common_schemas.py`

**Action**: Copy verbatim. Same BaseModelKwargs import fix as above.

**Exports**: `HealthResponse`, `ReadinessResponse`, `ErrorResponse`

---

### 2.10 `src/fastapi_tools/auth/google.py`

**Source**: `src/project_name/webapp/services/auth_service.py`

**Action**: Copy. Fix imports:
```python
# before
from project_name.config.webapp import GoogleOAuthConfig, SessionConfig
from project_name.webapp.core.security import ...
from project_name.webapp.schemas.auth_schemas import ...
# after
from fastapi_tools.config import GoogleOAuthConfig, SessionConfig
from fastapi_tools.security import ...
from fastapi_tools.schemas.auth import ...
```

**Additional change**: `get_authorization_url()` must accept an optional
`redirect_uri: str | None = None` parameter (required by TG's dynamic redirect
URI pattern). When provided it overrides `self.oauth_config.redirect_uri`.
Same for `authenticate()` — pass through to `exchange_code_for_tokens()`.

```python
def get_authorization_url(
    self, redirect_uri: str | None = None
) -> tuple[str, str]:
    uri = redirect_uri or self.oauth_config.redirect_uri
    ...

async def exchange_code_for_tokens(
    self, code: str, redirect_uri: str | None = None
) -> dict:
    uri = redirect_uri or self.oauth_config.redirect_uri
    ...

async def authenticate(
    self, code: str, state: str, redirect_uri: str | None = None
) -> SessionData:
    ...
    tokens = await self.exchange_code_for_tokens(code, redirect_uri=redirect_uri)
```

**Exports**: `GoogleAuthService`, `SessionStore`

---

### 2.11 `src/fastapi_tools/dependencies.py`

**Source**: `src/project_name/webapp/core/dependencies.py`

**Action**: Copy. This file currently imports `get_webapp_params` and
`get_project_name_paths` from the project. These are project-specific.

**Change**: Remove the `get_settings()` function (it calls `get_webapp_params()`
which is project-specific). Projects supply their own `get_settings` and pass
it via dependency override or app state. Everything else is generic:

```python
# Keep as-is (no project-specific imports):
get_session_store(request)
get_current_session(request, session)
get_current_user(session)
get_optional_user(session)
get_db_session()

# Remove from fastapi-tools (project supplies this):
# get_settings()  ← DELETE
```

Projects that need `get_settings` define their own one-liner using
`lru_cache` + their own params class, which is already how the template does it.

**Exports**: `get_session_store`, `get_current_session`, `get_current_user`,
`get_optional_user`, `get_db_session`

---

### 2.12 `src/fastapi_tools/templating.py`

**Source**: `src/project_name/webapp/core/templating.py`

**Action**: The current version hard-codes the templates path via
`get_project_name_paths()`. This must be made injectable.

**Change**: Accept the templates directory as a parameter. The `templates`
module-level singleton becomes a factory:

```python
# fastapi_tools/templating.py
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
from starlette.templating import Jinja2Templates

if TYPE_CHECKING:
    from fastapi_tools.config import WebappConfig

def make_templates(templates_dir: Path | str) -> Jinja2Templates:
    """Create a Jinja2Templates instance for the given directory."""
    return Jinja2Templates(directory=str(templates_dir))

def configure_templates(templates: Jinja2Templates, config: WebappConfig) -> None:
    """Inject application-wide globals into the Jinja2 environment."""
    templates.env.globals.update({
        "app_name": config.app_name,
        "app_version": config.app_version,
        "debug": config.debug,
    })
```

**Exports**: `make_templates`, `configure_templates`

---

### 2.13 `src/fastapi_tools/routers/health.py`

**Source**: `src/project_name/webapp/routers/health_router.py`

**Action**: Copy. Remove dependency on `get_settings()` from project params.
Health router reads version from the passed config via `request.app.state.config`:

```python
# before
from project_name.webapp.core.dependencies import get_settings
settings = get_settings()
return HealthResponse(status="healthy", version=settings.app_version, ...)

# after
from fastapi import Request
config: WebappConfig = request.app.state.config
return HealthResponse(status="healthy", version=config.app_version, ...)
```

**Exports**: `router` (APIRouter, prefix `/health`)

---

### 2.14 `src/fastapi_tools/routers/auth.py`

**Source**: `src/tg_central_hub_bot/webapp/routers/auth_router.py` (TG version —
this is the superset with dynamic `redirect_uri`)

**Action**: Copy. Fix all imports to `fastapi_tools.*`. Remove `get_settings`
dependency from project — read from `request.app.state.config` instead:

```python
# before
settings = get_settings()
redirect_uri = get_public_base_url(request, settings.public_base_url) + "/auth/google/callback"

# after
from fastapi_tools.config import WebappConfig
config: WebappConfig = request.app.state.config
redirect_uri = get_public_base_url(request, config.public_base_url) + "/auth/google/callback"
```

**Exports**: `router` (APIRouter, prefix `/auth`)

---

### 2.15 `src/fastapi_tools/factory.py`

**Source**: `src/tg_central_hub_bot/webapp/main.py` (TG version — superset with
`TrustedHostMiddleware` + `ProxyHeadersMiddleware`)

**Action**: Extract `create_app()` and `register_exception_handlers()` into the
library. Make it generic by removing all project-specific router/path references.

**Signature change**:

```python
def create_app(
    config: WebappConfig,
    *,
    extra_routers: list[APIRouter] | None = None,
    static_dir: Path | str | None = None,
    templates_dir: Path | str | None = None,
    lifespan: Callable | None = None,
) -> FastAPI:
    """Create and configure a FastAPI application.

    Args:
        config: Webapp configuration.
        extra_routers: Additional routers to include (project-specific).
        static_dir: Path to static files directory. If None, /static not mounted.
        templates_dir: Path to templates directory. If None, templating not configured.
        lifespan: Custom lifespan context manager. If None, a default is used
                  that initialises SessionStore and GoogleAuthService only.

    Returns:
        Configured FastAPI application instance.
    """
```

**What the factory always does** (not configurable):
- Creates `FastAPI` instance with `docs_url=None`, `redoc_url=None`
- Registers `CORSMiddleware` from `config.cors`
- Calls `setup_middleware(app, config)` (RequestID, SecurityHeaders, Logging)
- Adds `TrustedHostMiddleware(allowed_hosts=["*"] if config.debug else config.trusted_hosts)`
- Adds `ProxyHeadersMiddleware(trusted_hosts=["127.0.0.1", "::1"])`
- Registers all exception handlers (NotAuthenticated, NotAuthorized, RateLimit, generic)
- Includes `health_router` and `auth_router` always
- Registers self-hosted `/docs` and `/redoc` routes when `config.debug`

**What the factory does conditionally**:
- Mounts `/static` if `static_dir` provided
- Calls `configure_templates(templates, config)` if `templates_dir` provided
- Includes each router in `extra_routers`
- Uses `lifespan` if provided, else uses a default lifespan that only sets up
  `SessionStore` and `GoogleAuthService`

**Exports**: `create_app`, `default_lifespan`

---

### 2.16 `src/fastapi_tools/__init__.py`

Re-export the most commonly used symbols for convenience:

```python
from fastapi_tools.config import WebappConfig, GoogleOAuthConfig, SessionConfig
from fastapi_tools.factory import create_app
from fastapi_tools.exceptions import (
    NotAuthenticatedException,
    NotAuthorizedException,
    RateLimitExceededException,
)
from fastapi_tools.dependencies import get_current_user, get_optional_user
```

---

## 3. Full `src/fastapi_tools/` directory tree

```
src/fastapi_tools/
├── __init__.py
├── config.py            WebappConfig and sub-configs
├── factory.py           create_app(), default_lifespan()
├── middleware.py         RequestIDMiddleware, SecurityHeadersMiddleware,
│                         RequestLoggingMiddleware, setup_middleware()
├── security.py           TokenManager, generate_session_id, etc.
├── exceptions.py         Custom HTTPExceptions
├── dependencies.py       get_current_user, get_optional_user, etc.
├── templating.py         make_templates(), configure_templates()
├── auth/
│   ├── __init__.py
│   └── google.py         GoogleAuthService, SessionStore
├── routers/
│   ├── __init__.py
│   ├── auth.py           /auth/* endpoints
│   └── health.py         /health/* endpoints
├── schemas/
│   ├── __init__.py
│   ├── auth.py           SessionData, UserResponse, etc.
│   └── common.py         HealthResponse, ErrorResponse, etc.
├── models/
│   ├── __init__.py
│   └── base.py           BaseModelKwargs
└── utils/
    ├── __init__.py
    ├── singleton.py      Singleton metaclass
    └── url.py            get_public_base_url()
```

---

## 4. Changes to `python-project-template`

### 4.1 `pyproject.toml`

Add `fastapi-tools` to the `webapp` optional dependency group.
Remove individual webapp deps (fastapi, uvicorn, itsdangerous, etc.) from that
group since they become transitive via `fastapi-tools`:

```toml
[project.optional-dependencies]
webapp = [
    "fastapi-tools>=0.1.0",
]
```

Keep non-webapp deps (`haystack-ai`, `openai`, etc.) in `[project.dependencies]`
as-is — those are template defaults that each project trims.

### 4.2 `src/project_name/webapp/main.py`

Replace the current ~200-line factory with a thin wrapper:

```python
"""FastAPI application factory for project_name."""

from fastapi import FastAPI
from fastapi_tools import create_app

from project_name.params.project_name_params import get_project_name_paths
from project_name.params.project_name_params import get_webapp_params
from project_name.webapp.routers.pages_router import router as pages_router


def build_app() -> FastAPI:
    params = get_webapp_params()
    config = params.to_config()
    paths = get_project_name_paths()

    return create_app(
        config=config,
        extra_routers=[pages_router],
        static_dir=paths.static_fol,
        templates_dir=paths.templates_fol,
    )
```

### 4.3 `src/project_name/webapp/app.py`

Update entrypoint to call `build_app()`:

```python
from project_name.webapp.main import build_app

app = build_app()
```

### 4.4 `src/project_name/webapp/core/`

**Delete entirely** — all files move to `fastapi-tools`:
- `middleware.py` → `fastapi_tools/middleware.py`
- `security.py` → `fastapi_tools/security.py`
- `exceptions.py` → `fastapi_tools/exceptions.py`
- `dependencies.py` → `fastapi_tools/dependencies.py`
- `templating.py` → `fastapi_tools/templating.py`

### 4.5 `src/project_name/webapp/services/auth_service.py`

**Delete** — moves to `fastapi_tools/auth/google.py`.

### 4.6 `src/project_name/webapp/schemas/`

**Delete**:
- `auth_schemas.py` → `fastapi_tools/schemas/auth.py`
- `common_schemas.py` → `fastapi_tools/schemas/common.py`

### 4.7 `src/project_name/webapp/routers/health_router.py` and `auth_router.py`

**Delete** — both move to `fastapi_tools/routers/`.

### 4.8 `src/project_name/webapp/routers/pages_router.py`

**Keep** — this is project-specific (landing, dashboard, error pages).

Update its imports:
```python
# before
from project_name.webapp.core.dependencies import get_current_user, get_optional_user
from project_name.webapp.core.templating import templates
from project_name.webapp.schemas.auth_schemas import SessionData
# after
from fastapi_tools.dependencies import get_current_user, get_optional_user
from fastapi_tools.schemas.auth import SessionData
# templates instance now comes from app state, passed in by factory
```

The `pages_router` should get the `Jinja2Templates` instance via
`request.app.state.templates` (set by the factory when `templates_dir` is
provided) rather than a module-level import — this removes the circular path
dependency:

```python
# in each page handler
templates = request.app.state.templates
return templates.TemplateResponse(...)
```

### 4.9 `src/project_name/webapp/services/user_service.py`

**Keep** — it's a placeholder for project-specific user persistence.

Update its imports:
```python
# before
from project_name.webapp.schemas.auth_schemas import GoogleUserInfo, UserResponse
# after
from fastapi_tools.schemas.auth import GoogleUserInfo, UserResponse
```

### 4.10 `src/project_name/config/webapp/webapp_config.py`

**Delete** — `WebappConfig` and all sub-configs now come from `fastapi_tools.config`.

### 4.11 `src/project_name/params/webapp/webapp_params.py`

**Keep** — this is project-specific env loading.

Update imports:
```python
# before
from project_name.config.webapp import CORSConfig, GoogleOAuthConfig, ...
# after
from fastapi_tools.config import CORSConfig, GoogleOAuthConfig, WebappConfig, ...
```

### 4.12 `src/project_name/data_models/basemodel_kwargs.py`

**Keep a re-export shim** so existing project code doesn't break immediately,
but mark as deprecated in a comment:

```python
# Kept for backwards compat — import from fastapi_tools.models.base directly
from fastapi_tools.models.base import BaseModelKwargs as BaseModelKwargs
```

### 4.13 `src/project_name/metaclasses/singleton.py`

Same re-export shim:
```python
from fastapi_tools.utils.singleton import Singleton as Singleton
```

### 4.14 `tests/webapp/`

Update all test imports from `project_name.webapp.core.*` / `project_name.webapp.schemas.*`
to `fastapi_tools.*`. The tests themselves (logic for auth, health, pages, security)
stay in the template — they test that the wiring works, not the library internals.
`fastapi-tools` will have its own test suite.

### 4.15 `meta/rename_project.py` → copier

Out of scope for this PR. Tracked separately. The rename script stays functional
in the meantime.

---

## 5. File disposition summary

| File | Action |
|---|---|
| `webapp/core/middleware.py` | **Move** → `fastapi_tools/middleware.py` |
| `webapp/core/security.py` | **Move** → `fastapi_tools/security.py` |
| `webapp/core/exceptions.py` | **Move** → `fastapi_tools/exceptions.py` |
| `webapp/core/dependencies.py` | **Move** → `fastapi_tools/dependencies.py` (remove `get_settings`) |
| `webapp/core/templating.py` | **Move** → `fastapi_tools/templating.py` (make injectable) |
| `webapp/main.py` | **Replace** with thin `build_app()` wrapper |
| `webapp/app.py` | **Update** to call `build_app()` |
| `webapp/services/auth_service.py` | **Move** → `fastapi_tools/auth/google.py` |
| `webapp/services/user_service.py` | **Keep**, update imports |
| `webapp/routers/auth_router.py` | **Move** → `fastapi_tools/routers/auth.py` (use TG version) |
| `webapp/routers/health_router.py` | **Move** → `fastapi_tools/routers/health.py` |
| `webapp/routers/pages_router.py` | **Keep**, update imports, use `request.app.state.templates` |
| `webapp/schemas/auth_schemas.py` | **Move** → `fastapi_tools/schemas/auth.py` |
| `webapp/schemas/common_schemas.py` | **Move** → `fastapi_tools/schemas/common.py` |
| `config/webapp/webapp_config.py` | **Delete**, superseded by `fastapi_tools/config.py` |
| `params/webapp/webapp_params.py` | **Keep**, update imports |
| `data_models/basemodel_kwargs.py` | **Keep** as re-export shim |
| `metaclasses/singleton.py` | **Keep** as re-export shim |
| `utils/url_utils.py` (TG only) | **Move** → `fastapi_tools/utils/url.py` |
| `webapp/utils/` (TG only) | **Delete** after move |

---

## 6. Non-goals for this phase

These are **explicitly out of scope** and tracked separately:

- Telegram repo changes — do not touch
- `meta/rename_project.py` → copier migration
- `social-media-downloader` new repo
- Recipe service / recipinator / recipamatic consolidation
- LLM tools / laife extraction

---

## 7. Implementation order

1. Create `fastapi-tools` repo and bootstrap with uv/ruff/pre-commit
2. Implement all `src/fastapi_tools/` files (sections 2.1–2.16) with their own tests
3. Publish locally (`uv add ../fastapi-tools` path dependency for dev)
4. Update `python-project-template` (section 4) against the local path dep
5. Run template test suite — all tests must pass
6. Tag `fastapi-tools` `v0.1.0`, publish to PyPI or use as git dep
7. Update template to use tagged version
