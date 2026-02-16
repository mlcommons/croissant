"""Module to manage "bounding boxes" annotations on images."""

from typing import Any


def parse(value: Any) -> list[float]:
    """Parses a value to a machine-readable bounding box.

    Args:
        value: The value to parse can be either a single space-separated string or a
            list of float-compatible elements.

    Returns:
        The 4-float list that composes the bounding box.
    """
    if isinstance(value, list):
        pass
    elif isinstance(value, str):
        value = value.split(" ")
    else:
        raise ValueError(
            "Wrong format for a bounding box. Expected: str | list. Got:"
            f" {type(value)}. If you need to support more format, feel free to create"
            " an issue on GitHub."
        )
    try:
        value = [float(element) for element in value]
    except ValueError as e:
        raise ValueError(
            "Bounding boxes should have coordinates that can be converted to floats."
            f" Got {value}"
        ) from e
    if len(value) != 4:
        raise ValueError(
            "Bounding box could not be parsed. Bounding boxes should have a length of"
            f" 4. Got {len(value)}"
        )
    return value
