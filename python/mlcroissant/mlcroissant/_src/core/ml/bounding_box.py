"""Module to manage "bounding boxes" annotations on images."""

from typing import Any, List

def _parse_one(value: Any) -> List[float]:
    """Parses a single bounding box from various formats."""
    # Handle nested list case, e.g., [[0.1, 0.2, 0.3, 0.4]]
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], list):
            value = value[0]
    # Handle space-separated string case
    elif isinstance(value, str):
        value = value.split(" ")

    # The value should now be a simple list of coordinates
    if not isinstance(value, list):
        raise TypeError(f"Cannot parse a single bounding box from type {type(value)}")

    if len(value) != 4:
        raise ValueError(
            "A single bounding box must have exactly 4 coordinates. "
            f"Got {len(value)} for value: {value}"
        )
    
    try:
        # Convert all elements to float and return
        return [float(coord) for coord in value]
    except (ValueError, TypeError) as e:
        raise ValueError(
            "Bounding box coordinates must be convertible to floats. "
            f"Got {value}"
        ) from e

def _parse_all(value: List) -> List[List[float]]:
    """Parses a list containing multiple bounding boxes."""
    if not value:
        return []

    # Case 1: List of lists, e.g., [[box1], [box2]]
    if isinstance(value[0], list):
        return [_parse_one(item) for item in value]
    
    # Case 2: Flat list, e.g., [x1, y1, w1, h1, x2, y2, w2, h2, ...]
    if len(value) % 4 != 0:
        raise ValueError(
            "A flat list of bounding box coordinates must have a length "
            f"that is a multiple of 4. Got length {len(value)}."
        )
    
    try:
        coords = [float(v) for v in value]
        # Chunk the flat list into a list of 4-element lists
        return [coords[i:i + 4] for i in range(0, len(coords), 4)]
    except (ValueError, TypeError) as e:
        raise ValueError(
            "All elements in the flat list must be convertible to float."
        ) from e


def parse(value: Any) -> List[List[float]]:
    """
    Parses a value into a list of one or more bounding boxes.

    This function determines whether the input represents a single bounding box
    or multiple, and delegates to the appropriate parser.

    Args:
        value: The value to parse. Can be:
            - A single space-separated string: "x y w h"
            - A list representing one box: [x, y, w, h] or [[x, y, w, h]]
            - A list of lists for multiple boxes: [[box1], [box2], ...]
            - A flat list for multiple boxes: [x1, y1, w1, h1, x2, ...]

    Returns:
        A list of bounding boxes, where each box is a 4-float list.
        e.g., [[25.0, 30.0, 100.0, 150.0]]
    """
    # Strings are always treated as a single bounding box
    if isinstance(value, str):
        return [_parse_one(value)]

    if isinstance(value, list):
        if not value:
            return []

        # Determine parsing strategy based on list structure and length
        is_list_of_lists = isinstance(value[0], list)
        is_flat_list_of_many = len(value) > 4 and len(value) % 4 == 0

        if is_list_of_lists or is_flat_list_of_many:
            print(f"Parsing multiple bounding boxes from: {value}")
            return _parse_all(value)
        else:
            # Otherwise, treat as a single bounding box
            print(f"Parsing single bounding box from: {value}")
            return [_parse_one(value)]

    raise TypeError(
        "Wrong format for a bounding box. Expected: str | list. "
        f"Got: {type(value)}."
    )