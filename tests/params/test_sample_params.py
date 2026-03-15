"""Test the SampleParams class."""

from fastapi_tools.config.sample_config import SampleConfig
from fastapi_tools.params.sample_params import SampleParams


def test_sample_params_init() -> None:
    """Test initialization of SampleParams."""
    params = SampleParams()
    assert params.some_int == 42
    assert params.nested_model_some_str == "Hello, Params!"
    assert params.custom_kwargs == {"key1": "value1", "key2": "value2"}


def test_sample_params_to_config() -> None:
    """Test conversion to SampleConfig."""
    params = SampleParams()
    config = params.to_config()

    assert isinstance(config, SampleConfig)
    assert config.some_int == 42
    assert config.nested_model.some_str == "Hello, Params!"
    assert config.kwargs == {"key1": "value1", "key2": "value2"}


def test_sample_params_str() -> None:
    """Test string representation."""
    params = SampleParams()
    s = str(params)
    assert "SampleParams:" in s
    assert "some_int: 42" in s
