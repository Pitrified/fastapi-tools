"""Test the fastapi_tools paths."""

from fastapi_tools.params.fastapi_tools_params import get_fastapi_tools_paths


def test_fastapi_tools_paths() -> None:
    """Test the fastapi_tools paths."""
    fastapi_tools_paths = get_fastapi_tools_paths()
    assert fastapi_tools_paths.src_fol.name == "fastapi_tools"
    assert fastapi_tools_paths.root_fol.name == "fastapi-tools"
    assert fastapi_tools_paths.data_fol.name == "data"
