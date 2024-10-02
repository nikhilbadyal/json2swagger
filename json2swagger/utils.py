"""Common utility functions."""
import json
from typing import Any

from typing_extensions import NotRequired, Self, TypedDict


class JSONDict(dict[str, Any]):
    """Custom JSONN Dict."""

    def __str__(self: Self) -> str:
        """Override the __str__ method to print JSON."""
        return json.dumps(self, indent=4, default=str)


class Documentation(TypedDict):
    """Writer parameters."""

    summary: NotRequired[str]
    description: NotRequired[str]
    operationId: NotRequired[str]


class Responses(TypedDict):
    """Resppnses parameters."""

    status: NotRequired[str]


class Method(TypedDict):
    """API Methods."""

    summary: NotRequired[str]
    description: NotRequired[str]
    operationId: NotRequired[str]
    responses: NotRequired[Any]
    parameters: NotRequired[Any]
    requestBody: NotRequired[Any]
