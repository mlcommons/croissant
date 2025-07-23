"""Module to manage "bounding boxes" annotations on images."""

from typing import Any, List, Union


def _parse_one(value: Union[str, List[Any]]) -> List[float]:
    """Parse a single bounding box representation into a list of four floats."""
    processed_value = []
    if isinstance(value, str):
        processed_value = value.split()
    elif isinstance(value, list):
        processed_value = value

    if len(processed_value) != 4:
        raise ValueError(
            f"Input should have a length of 4, but has length {len(processed_value)}."
        )

    try:
        return [float(coord) for coord in processed_value]
    except ValueError as e:
        raise ValueError(
            "All bounding box coordinates can be converted to floats. "
            f"Got: {processed_value}"
        ) from e


def _parse_all(value: List) -> List[List[float]]:
    """Parse a list containing multiple bounding boxes."""
    # Case 1: List of lists, e.g., [[box1], [box2]]
    if isinstance(value[0], list):
        return [_parse_one(item) for item in value]

    # Case 2: Flat list, e.g., [x1, y1, w1, h1, x2, y2, w2, h2]
    # This case is handled by the main parse function's dispatch logic.
    # We chunk the flat list into a list of 4-element lists.
    try:
        coords = [float(v) for v in value]
        return [coords[i : i + 4] for i in range(0, len(coords), 4)]
    except ValueError as e:
        raise ValueError(
            f"All bounding box coordinates can be converted to floats. Got: {value}"
        ) from e


def parse(value: Any) -> Union[List[float], List[List[float]]]:
    """Parse a value into one or more bounding boxes.

    The return type depends on the input:
    - A single bounding box returns a List[float].
    - Multiple bounding boxes returns a List[List[float]].

    Args:
        value: The value to parse. Can be a string, a list of 4 elements,
               a list of lists, or a flat list of 4*N elements.

    Returns:
        A list of four floats, or a list of such lists.

    Raises:
        ValueError: If the input format is invalid.
    """
    if isinstance(value, str):
        return _parse_one(value)

    if isinstance(value, list):
        if not value:
            return []

        # Decide if we're parsing one or multiple boxes.
        if isinstance(value[0], list):
            # A list of lists is always multiple bounding boxes.
            return _parse_all(value)
        else:
            # A flat list. Check length to decide.
            if len(value) % 4 == 0:
                if len(value) == 4:
                    # A list of 4 items is a single bounding box.
                    return _parse_one(value)
                else:
                    # A list of 4*N items is multiple bounding boxes.
                    return _parse_all(value)

    # If the input is not a string or a list, or if it's a list with
    # an invalid length (e.g., 5), we let _parse_one raise the
    # appropriate, specific error.
    if isinstance(value, list) and len(value) != 4:
        return _parse_one(value)

    raise ValueError(f"Wrong format. Expected str or list, but got {type(value)}.")
