"""Test that the environment variables are available."""

import os


def test_env_vars() -> None:
    """The environment var FASTAPI_TOOLS_SAMPLE_ENV_VAR is available."""
    assert "FASTAPI_TOOLS_SAMPLE_ENV_VAR" in os.environ
    assert os.environ["FASTAPI_TOOLS_SAMPLE_ENV_VAR"] == "sample"
