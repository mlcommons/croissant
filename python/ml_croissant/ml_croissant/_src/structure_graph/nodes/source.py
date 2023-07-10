"""Source module."""

import dataclasses
import re
from typing import Any

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import ID_REGEX, validate_name


def parse_reference(issues: Issues, source_data: str) -> tuple[str, ...]:
    source_regex = re.compile(rf"^\#\{{({ID_REGEX})(?:\/([^\/]+))*\}}$")
    match = source_regex.match(source_data)
    if match is None:
        issues.add_error(
            f"Malformed source data: {source_data}. The source data should be written"
            " as `#{name}` where name is valid ID."
        )
        return ()
    groups = tuple(group for group in match.groups() if group is not None)
    # Only validate the root group, because others can point to external columns
    # (like in a CSV) with fuzzy names.
    validate_name(issues, groups[0])
    return groups


@dataclasses.dataclass(frozen=True)
class Source:
    """Standardizes the usage of sources.

    Croissant accepts several manners to declare sources:

    Either as a simple reference:

    ```json
    "source": "#{name_of_the_source.name_of_the_field}"
    ```

    Or jointly with transform operations:

    ```json
    "source": {
        "data": "#{name_of_the_source}",
        "applyTransform": {
            "format": "yyyy-MM-dd HH:mm:ss.S",
            "regex": "([^\\/]*)\\.jpg",
            "separator": "|"
        }
    }
    ```
    """

    reference: tuple[str, ...] = ()
    apply_transform_regex: str | None = None
    apply_transform_separator: str | None = None

    @classmethod
    def from_json_ld(cls, issues: Issues, field: Any) -> "Source":
        if isinstance(field, str):
            return cls(reference=parse_reference(issues, field))
        elif isinstance(field, dict):
            try:
                apply_transform = field.get("apply_transform", {})
                return cls(
                    reference=parse_reference(issues, field.get("data")),
                    apply_transform_regex=apply_transform.get("regex"),
                    apply_transform_separator=apply_transform.get("separator"),
                )
            except (IndexError, TypeError) as exception:
                issues.add_error(
                    f"Malformed `source`: {field}. Got exception: {exception}"
                )
                return cls(reference=())
        else:
            issues.add_error(f"`source` has wrong type: {type(field)} ({field})")
            return cls(reference=())

    def __bool__(self):
        """Allows to write `if not node.source` / `if node.source`"""
        return len(self.reference) > 0
