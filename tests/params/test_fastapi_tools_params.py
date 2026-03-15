"""Test the FastapiToolsParams class."""

from fastapi_tools.params.fastapi_tools_params import FastapiToolsParams
from fastapi_tools.params.fastapi_tools_params import get_fastapi_tools_params
from fastapi_tools.params.fastapi_tools_paths import FastapiToolsPaths
from fastapi_tools.params.sample_params import SampleParams


def test_fastapi_tools_params_singleton() -> None:
    """Test that FastapiToolsParams is a singleton."""
    params1 = FastapiToolsParams()
    params2 = FastapiToolsParams()
    assert params1 is params2
    assert get_fastapi_tools_params() is params1


def test_fastapi_tools_params_init() -> None:
    """Test initialization of FastapiToolsParams."""
    params = FastapiToolsParams()
    assert isinstance(params.paths, FastapiToolsPaths)
    assert isinstance(params.sample, SampleParams)


def test_fastapi_tools_params_str() -> None:
    """Test string representation."""
    params = FastapiToolsParams()
    s = str(params)
    assert "FastapiToolsParams:" in s
    assert "FastapiToolsPaths:" in s
    assert "SampleParams:" in s
