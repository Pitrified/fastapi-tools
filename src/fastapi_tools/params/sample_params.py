"""Values for sample params of sample config."""

from fastapi_tools.config.sample_config import NestedModel
from fastapi_tools.config.sample_config import SampleConfig


class SampleParams:
    """Sample params for sample config."""

    def __init__(self) -> None:
        """Load the sample params."""
        self.some_int: int = 42
        self.nested_model_some_str: str = "Hello, Params!"
        self.custom_kwargs: dict = {"key1": "value1", "key2": "value2"}

    def to_config(self) -> SampleConfig:
        """Convert params to config."""
        return SampleConfig(
            some_int=self.some_int,
            nested_model=NestedModel(
                some_str=self.nested_model_some_str,
            ),
            kwargs=self.custom_kwargs,
        )

    def __str__(self) -> str:
        """Return the string representation of the object."""
        s = "SampleParams:"
        s += f"\n  some_int: {self.some_int}"
        s += f"\n  nested_model_some_str: {self.nested_model_some_str}"
        s += f"\n  custom_kwargs: {self.custom_kwargs}"
        return s
