"""Base node module."""

from __future__ import annotations

import abc
import dataclasses
import json
import re
from typing import Any

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.types import Json

ID_REGEX = "[a-zA-Z0-9\\-_\\.]+"
_MAX_ID_LENGTH = 255


@dataclasses.dataclass(eq=False, repr=False)
class Node(abc.ABC):
    """Structure node in Croissant.

    This generic class will be inherited by the actual Croissant nodes:
    - Field
    - FileObject
    - FileSet
    - Metadata
    - RecordSet

    When building the node, `self.context.issues` are populated when issues are
    encountered.

    Args:
        issues: the issues that will be modified in-place.
        context: the context of the node in the JSON-LD structure (see `Context` class).
        folder: The path of the Croissant folder.
        name: The name of the node.
        graph: The structure graph as a `nx.MultiDiGraph`.
        parents: The parent nodes in the Croissant JSON-LD as a tuple.
    """

    ctx: Context = dataclasses.field(default_factory=Context)
    name: str = ""
    parents: list[Node] = dataclasses.field(default_factory=list, init=False)

    def __post_init__(self):
        """Checks for `name` (common property between all nodes)."""
        self.assert_has_mandatory_properties("name")

    def assert_has_mandatory_properties(self, *mandatory_properties: str):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            mandatory_properties: A list of mandatory properties for the current node.
                If the node doesn't have one, it triggers an error.
        """
        for mandatory_property in mandatory_properties:
            value = getattr(self, mandatory_property)
            if not value:
                error = (
                    "Property"
                    f' "{constants.FROM_CROISSANT(self.ctx).get(mandatory_property)}"'
                    " is mandatory, but does not exist."
                )
                self.add_error(error)

    def assert_has_optional_properties(self, *optional_properties: str):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            optional_properties: A list of optional properties for the current node. If
                the node doesn't have one, it triggers a warning.
        """
        for optional_property in optional_properties:
            value = getattr(self, optional_property)
            if not value:
                error = (
                    "Property"
                    f' "{constants.FROM_CROISSANT(self.ctx).get(optional_property)}" is'
                    " recommended, but does not exist."
                )
                self.add_warning(error)

    def assert_has_exclusive_properties(self, *exclusive_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            exclusive_properties: A list of list of exclusive properties: the current
                node should have at least one.
        """
        for possible_exclusive_properties in exclusive_properties:
            if not self.there_exists_at_least_one_property(
                possible_exclusive_properties
            ):
                error = (
                    "At least one of these properties should be defined:"
                    f" {possible_exclusive_properties}."
                )
                self.add_error(error)

    def get_issue_context(self) -> str:
        """Adds context to an issue by printing metadata(...) > ... > field(...)."""
        nodes = self.parents + [self]
        return " > ".join(f"{type(node).__name__}({node.name})" for node in nodes)

    def add_error(self, error: str):
        """Adds a new error."""
        self.ctx.issues.add_error(error, self)

    def add_warning(self, warning: str):
        """Adds a new warning."""
        self.ctx.issues.add_warning(warning, self)

    def __repr__(self) -> str:
        """Prints a simplified string representation of the node: `Node(uid="xxx")`."""
        return f'{self.__class__.__name__}(uid="{self.uid}")'

    @property
    def uid(self) -> str:
        """Unique identifier for the node.

        For fields, the UID is the path from their RecordSet. For other nodes, it is
        their names.
        """
        if len(self.parents) <= 1:
            return self.name
        return f"{self.parents[-1].uid}/{self.name}"

    @property
    def parent(self) -> Node | None:
        """Direct parent of the node or None if no parent."""
        if not self.parents:
            return None
        return self.parents[-1]

    @property
    def predecessors(self) -> set[Node]:
        """Predecessors in the structure graph."""
        return set(self.ctx.graph.predecessors(self))

    @property
    def successors(self) -> tuple[Node, ...]:
        """Successors in the structure graph."""
        if self not in self.ctx.graph:
            return ()
        # We use tuples in order to have a hashable data structure to be put in input of
        # operations.
        return tuple(self.ctx.graph.successors(self))

    @property
    def issues(self) -> Issues:
        """Shortcut to access issues in node."""
        return self.ctx.issues

    @abc.abstractmethod
    def to_json(self) -> Json:
        """Converts the node to JSON."""
        ...

    @classmethod
    @abc.abstractmethod
    def from_jsonld(cls, *args, **kwargs) -> Any:
        """Creates a node from JSON-LD."""
        ...

    def validate_name(self):
        """Validates the name (which are used as unique identifiers in Croissant)."""
        name = self.name
        if not isinstance(name, str):
            self.add_error(f"The identifier should be a string. Got: {type(name)}.")
            return
        if not name:
            # This case is already checked for in every node's __post_init__ as `name`
            # is a mandatory parameter.
            return
        if len(name) > _MAX_ID_LENGTH:
            self.add_error(
                f'The identifier "{name}" is too long (>{_MAX_ID_LENGTH} characters).'
            )
        regex = re.compile(rf"^{ID_REGEX}$")
        if not regex.match(name):
            self.add_error(f'The identifier "{name}" contains forbidden characters.')

    def there_exists_at_least_one_property(self, possible_properties: list[str]):
        """Checks for the existence of one of `possible_properties` in `keys`."""
        for possible_property in possible_properties:
            if getattr(self, possible_property, None) is not None:
                return True
        return False

    def __hash__(self):
        """Hashes all immutable arguments."""
        args = []
        for field in dataclasses.fields(self):
            # Do not hash children, graphs, issues and context:
            if field.name not in (
                "context",
                "creators",
                "distribution",
                "fields",
                "graph",
                "issues",
                "mapping",
                "parents",
                "rdf",
                "record_sets",
                "sub_fields",
            ):
                # If the code failed here, you probably added an unhashable property
                # that should appear in the allow list above.
                try:
                    args.append(_make_hashable(getattr(self, field.name)))
                except TypeError:
                    pass
        return hash(tuple(args))

    def __eq__(self, other: Any) -> bool:
        """Compares two Nodes given their arguments."""
        if type(self) is not type(other):
            return False
        return hash(self) == hash(other)


def _make_hashable(arg: Any) -> Any:
    if isinstance(arg, (dict, list)):
        return json.dumps(arg)
    else:
        return arg
