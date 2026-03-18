# Fix redirect URI mismatch error

## Overview

when running the app from `python-project-template` with Google OAuth enabled, I get the following error:

```
~/repos/python-project-template (feat/fastapi_tools_setup)$ uv run uvicorn project_name.webapp.app:app --reload
```

```
You can’t sign in because this app sent an invalid request. You can try again later, or contact the developer about this issue. Learn more about this error
If you are a developer of this app, see error details.
Error 400: redirect_uri_mismatch
```

on google cloud console

```
Authorized JavaScript origins
http://localhost:8000

Authorized redirect URIs
http://localhost:8000/auth/google/callback
https://entries.pitrified.qzz.io/auth/google/callback
```

in `.env`, only GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET_KEY are set

update
`python-project-template/docs/guides/webapp_setup.md`
if needed.

## Plan

### Root Cause

The `redirect_uri_mismatch` has two compounding causes:

1. **The auth router ignores the configured `redirect_uri`.**
   `google_login` and `google_callback` build the OAuth `redirect_uri` dynamically:
   ```python
   redirect_uri = get_public_base_url(request, config.public_base_url) + "/auth/google/callback"
   ```
   This is fragile: if the user accesses the app via `http://127.0.0.1:8000` instead of
   `http://localhost:8000`, or through any hostname that differs from what is registered in
   Google Console, the mismatch error fires before Google even shows the consent screen.

2. **`config.public_base_url` is always `None`.**
   `WebappParams.to_config()` never passes `public_base_url` to `WebappConfig`, so the
   `get_public_base_url` override is never used. The fallback is always the raw
   `request.url`, which is whatever the user typed in the browser.

3. **`GOOGLE_REDIRECT_URI` env var and `_get_default_redirect_uri()` are wired up in
   `WebappParams` and stored in `config.google_oauth.redirect_uri`, but the auth router
   completely ignores this pre-configured, stable value.**

### Fix

1. **`fastapi_tools/routers/auth.py`** - use `config.google_oauth.redirect_uri` directly
   in both `google_login` and `google_callback` instead of building dynamically with
   `get_public_base_url`. The configured value is stable, matches what is registered in
   Google Console, and respects `GOOGLE_REDIRECT_URI` env var in production. Remove the
   now-unused `get_public_base_url` import from the router (the function stays in
   `utils/url.py` for consumers who need it).

2. **`python-project-template/src/project_name/params/webapp/webapp_params.py`** - read
   `PUBLIC_BASE_URL` env var and propagate it to `WebappConfig.public_base_url`. This is
   a separate concern from `GOOGLE_REDIRECT_URI`: it lets the app know its public URL for
   generating absolute links in templates and API responses, without affecting the OAuth
   redirect URI.

3. **`python-project-template/docs/guides/webapp_setup.md`** - update the env var table
   and the troubleshooting section to clarify the roles of `GOOGLE_REDIRECT_URI` and
   `PUBLIC_BASE_URL`, and explain why the URI must exactly match the Google Console entry.
