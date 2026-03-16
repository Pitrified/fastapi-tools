"""Jinja2 template engine configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from starlette.templating import Jinja2Templates

if TYPE_CHECKING:
    from fastapi_tools.config import WebappConfig


def make_templates(templates_dir: Path | str) -> Jinja2Templates:
    """Create a Jinja2Templates instance for the given directory.

    Args:
        templates_dir: Path to the templates directory.

    Returns:
        Configured Jinja2Templates instance.
    """
    return Jinja2Templates(directory=str(templates_dir))


def configure_templates(templates: Jinja2Templates, config: WebappConfig) -> None:
    """Inject application-wide globals into the Jinja2 environment.

    Args:
        templates: Jinja2Templates instance to configure.
        config: Webapp configuration containing app metadata.
    """
    templates.env.globals.update(
        {
            "app_name": config.app_name,
            "app_version": config.app_version,
            "debug": config.debug,
        }
    )
