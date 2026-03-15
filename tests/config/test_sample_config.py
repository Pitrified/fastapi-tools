"""Test the SampleConfig class."""

from fastapi_tools.config.sample_config import NestedModel
from fastapi_tools.config.sample_config import SampleConfig


def test_sample_config_init() -> None:
    """Test initialization of SampleConfig."""
    nested = NestedModel(some_str="test")
    config = SampleConfig(some_int=1, nested_model=nested)

    assert config.some_int == 1
    assert config.nested_model.some_str == "test"
    assert config.kwargs == {}


def test_sample_config_with_kwargs() -> None:
    """Test initialization with kwargs."""
    nested = NestedModel(some_str="test")
    config = SampleConfig(
        some_int=1,
        nested_model=nested,
        kwargs={"extra": "value"},
    )

    assert config.kwargs == {"extra": "value"}


def test_sample_config_to_kw() -> None:
    """Test to_kw method inherited from BaseModelKwargs."""
    nested = NestedModel(some_str="test")
    config = SampleConfig(
        some_int=1,
        nested_model=nested,
        kwargs={"extra": "value"},
    )

    kw = config.to_kw()
    assert kw["some_int"] == 1
    assert kw["nested_model"] == nested
    assert kw["extra"] == "value"
    assert "kwargs" not in kw
