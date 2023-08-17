"""RecordSet module."""

import dataclasses
import json

from ml_croissant._src.core import constants
from ml_croissant._src.structure_graph.base_node import Node


@dataclasses.dataclass(frozen=True, repr=False)
class RecordSet(Node):
    """Nodes to describe a dataset RecordSet."""

    # `data` is passed as a string for the moment, because dicts and lists are not
    # hashable.
    data: str | None = None
    description: str | None = None
    key: str | None = None
    name: str = ""

    def check(self):
        """Implements checks on the node."""
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
        if self.data:
            data = json.loads(self.data)
            if not isinstance(data, list):
                self.add_error(
                    f"{constants.ML_COMMONS_DATA} should declare a list. Got:"
                    f" {type(data)}."
                )
                return
            if not data:
                self.add_error(
                    f"{constants.ML_COMMONS_DATA} should declare a non empty list."
                )
            fields = [
                node
                for node in self.graph.nodes
                if node.parent is not None and node.parent.uid == self.uid
            ]
            expected_keys = {field.name for field in fields}
            for i, line in enumerate(data):
                if not isinstance(line, dict):
                    self.add_error(
                        f"{constants.ML_COMMONS_DATA} should declare a list of dict."
                        f" Got: a list of {type(line)}."
                    )
                    return
                keys = set(line.keys())
                if keys != expected_keys:
                    self.add_error(
                        f"Line #{i} doesn't have the expected columns. Expected:"
                        f" {expected_keys}. Got: {keys}."
                    )
