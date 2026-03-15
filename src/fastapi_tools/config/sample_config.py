"""Sample config for the fastapi_tools project."""

from pydantic import Field

from fastapi_tools.data_models.basemodel_kwargs import BaseModelKwargs


class NestedModel(BaseModelKwargs):
    """Nested model for sample config."""

    some_str: str


class SampleConfig(BaseModelKwargs):
    """Sample config model."""

    some_int: int
    nested_model: NestedModel
    kwargs: dict = Field(default_factory=dict)
