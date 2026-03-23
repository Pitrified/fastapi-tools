# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-03-23

Initial release. Provides a reusable FastAPI scaffold with Google OAuth, session management,
CORS, rate limiting, Jinja2 templates, and security utilities.

### Added

**Webapp factory**
- `build_app()` / `create_app()` factory in `src/fastapi_tools/webapp/main.py` - wires up
  middleware, routers, exception handlers, static files, and Jinja2 templates.
- Entry point for uvicorn: `fastapi_tools.webapp.app:app`.

**Config / Params pattern**
- `BaseModelKwargs` - Pydantic base with `to_kw(exclude_none=True)` kwargs flattening.
- `Singleton` metaclass - one instance per process, reset-able in tests.
- `EnvType` + `EnvStageType` / `EnvLocationType` enums - `DEV`/`PROD` x `LOCAL`/`RENDER`
  environment dispatch.
- `FastapiToolsParams` singleton + `FastapiToolsPaths` - project-wide config and env-aware
  filesystem paths.
- `SampleParams` / `SampleConfig` - canonical reference implementations.
- `load_env()` - loads `~/cred/fastapi-tools/.env` via python-dotenv.

**Webapp config models**
- `CORSConfig`, `SessionConfig`, `RateLimitConfig`, `GoogleOAuthConfig`, `WebappConfig` - all
  extend `BaseModelKwargs` and live in `src/fastapi_tools/config/webapp/`.
- Self-hosted Swagger UI and ReDoc in `dev` mode (no external CDN).
