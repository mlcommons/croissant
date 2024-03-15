"""Versions module."""

from typing import Any

from mlcroissant._src.core.issues import ErrorException
from mlcroissant._src.core.issues import WarningException


def cast_version(version: Any) -> str | None:
    """Casts the dataset version and returns a normalized string version.

    A valid version follows Semantic Versioning 2.0.0 `MAJOR.MINOR.PATCH`.
    For more information: https://semver.org/spec/v2.0.0.html.
    """
    # Version is a recommended but not mandatory attribute.
    if version is None:
        return None

    if isinstance(version, str):
        numbers = version.split(".")
        are_not_all_numbers = any(not number.isnumeric() for number in numbers)
        if len(numbers) != 3 or are_not_all_numbers:
            raise WarningException(
                f"Version doesn't follow MAJOR.MINOR.PATCH: {version}. For more"
                " information refer to: https://semver.org/spec/v2.0.0.html"
            )
        return version
    elif isinstance(version, int):
        return f"{version}.0.0"
    elif isinstance(version, float):
        return f"{version}.0"
    raise ErrorException(
        f"The version should be a string or a number. Got: {type(version)}."
    )
