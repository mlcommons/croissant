"""Base node module."""

import dataclasses
import inspect
import re
from typing import Any, Callable

from rdflib import term
from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.issues import WarningException
from mlcroissant._src.core.json_ld import box_singleton_list
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.json_ld import sort_dict
from mlcroissant._src.core.json_ld import unbox_singleton_list
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.uuid import generate_uuid
from mlcroissant._src.core.uuid import uuid_from_jsonld

NAME_REGEX = "[a-zA-Z0-9\\-_\\.]+"
_MAX_NAME_LENGTH = 255
# This could also be an attribute of JsonldField:
_LIST_FIELDS = {"distribution", "fields", "record_sets"}
_MISSING_JSONLD_TYPE = "__MISSING_JSONLD_TYPE__"
MATCHING_TYPES = {
    SDO.Boolean: bool,
    SDO.Date: str,
    SDO.DateTime: str,
    SDO.Integer: int,
    SDO.Number: float,
    SDO.Text: str,
    SDO.Time: str,
    SDO.URL: str,
}


@dataclasses.dataclass(eq=False, repr=False)
class Node:
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
        ctx: the context containing the shared state between all nodes.
        name: The name of the node.
        parents: The parent nodes in the Croissant JSON-LD as a tuple.
    """

    ctx: Context = dataclasses.field(default_factory=Context)
    id: str = dataclasses.field(default_factory=generate_uuid)
    name: str | None = None
    parents: list["Node"] = dataclasses.field(default_factory=list)
    jsonld: Any = None

    def __post_init__(self):
        """Checks exclusive properties."""
        self._cast_fields()
        self._check_exclusive_properties()

    def _cast_fields(self):
        """Applies all `field.cast_fn`."""
        for field in mlc_dataclasses.jsonld_fields(self):
            if field.cast_fn:
                try:
                    value = getattr(self, field.name)
                    new_value = field.cast_fn(value)
                    setattr(self, field.name, new_value)
                except WarningException as e:
                    self.add_warning(repr(e))
                except Exception as e:
                    self.add_error(repr(e))

    def assert_has_mandatory_properties(self, *mandatory_properties: str):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            mandatory_properties: A list of mandatory properties for the current node.
                If the node doesn't have one, it triggers an error.
        """
        for mandatory_property in mandatory_properties:
            if hasattr(self, mandatory_property):
                value = getattr(self, mandatory_property)
                if not value:
                    error = (
                        "Property"
                        f' "{constants.FROM_CROISSANT(self.ctx).get(mandatory_property)}"'
                        " is mandatory, but does not exist."
                    )
                    self.add_error(error)
            else:
                self.add_error(
                    "mlcroissant checks for an inexisting property:"
                    f" {mandatory_property}"
                )

    def assert_has_optional_properties(self, *optional_properties: str):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            optional_properties: A list of optional properties for the current node. If
                the node doesn't have one, it triggers a warning.
        """
        for optional_property in optional_properties:
            if hasattr(self, optional_property):
                value = getattr(self, optional_property)
                if not value:
                    property = constants.FROM_CROISSANT(self.ctx).get(optional_property)
                    if property is None:
                        self.add_error(
                            "mlcroissant does not define property"
                            f' "{optional_property}" in constants.FROM_CROISSANT.'
                        )
                    else:
                        self.add_warning(
                            f'Property "{property}" is recommended, but does not exist.'
                        )
            else:
                self.add_error(
                    "mlcroissant checks for an inexisting property:"
                    f" {optional_property}"
                )

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

    def _check_exclusive_properties(self):
        """Checks exclusive properties on the node."""
        fields = {field.name: field for field in mlc_dataclasses.jsonld_fields(self)}
        for field in mlc_dataclasses.jsonld_fields(self):
            exclusive_with = field.exclusive_with
            if field.name in field.exclusive_with:
                raise ValueError(f'"{field.name}" appears in its own in exclusive_with')
            if field.exclusive_with:
                exclusive_fields = [field] + [
                    fields[name] for name in exclusive_with if name in fields
                ]
                properties = [getattr(self, field.name) for field in exclusive_fields]
                has_exactly_one_property = sum(bool(p) for p in properties) == 1
                if not has_exactly_one_property:
                    urls = [str(field.call_url(self.ctx)) for field in exclusive_fields]
                    name = self._jsonld_type(self.ctx) or self.__class__.__name__
                    self.ctx.issues.add_error(
                        f"{name} should have one of the following properties"
                        f" {' or '.join(urls)}."
                    )

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
        """Prints a simplified string representation of the node: `Node(uuid="xxx")`."""
        return f'{self.__class__.__name__}(uuid="{self.uuid}")'

    @property
    def uuid(self) -> str:
        """Unique identifier for the node.

        For Croissant <=0.8: for fields, the UID is the path from their RecordSet. For other
        nodes, it is their names.
        For Croissant <=1.0: it corresponds to the node's UUID.
        """
        if self.ctx.is_v0():
            if len(self.parents) <= 1:
                return self.name or ""
            return f"{self.parents[-1].uuid}/{self.name}"
        else:
            return self.id

    @property
    def parent(self) -> "Node | None":
        """Direct parent of the node or None if no parent."""
        if not self.parents:
            return None
        return self.parents[-1]

    @property
    def predecessors(self) -> set["Node"]:
        """Predecessors in the structure graph."""
        try:
            predecessors = self.ctx.graph.predecessors(self)
            return set(predecessors)  # pytype: disable=bad-return-type
        except KeyError as e:
            raise KeyError(
                f"Could not find node '{self.id}' in the graph. Make sure to build a"
                " full mlcroissant metadata object (mlc.Metadata) wrapping all the"
                " FileSets/FileObjects/RecordSets/Fields."
            ) from e

    @property
    def recursive_predecessors(self) -> set["Node"]:
        """Predecessors and predecessors of predecessors in the structure graph."""
        predecessors = set()
        for predecessor in self.predecessors:
            predecessors.add(predecessor)
            predecessors.update(predecessor.recursive_predecessors)
        return predecessors

    @property
    def predecessor(self) -> "Node | None":
        """First predecessor in the structure graph."""
        if not self.ctx.graph.has_node(self):
            return None
        return next(
            self.ctx.graph.predecessors(self), None
        )  # pytype: disable=bad-return-type

    @property
    def successors(self) -> tuple["Node", ...]:
        """Successors in the structure graph."""
        if self not in self.ctx.graph:
            return ()
        # We use tuples in order to have a hashable data structure to be put in input of
        # operations.
        return tuple(self.ctx.graph.successors(self))  # pytype: disable=bad-return-type

    @property
    def recursive_successors(self) -> set["Node"]:
        """Successors and successors of successors in the structure graph."""
        successors = set()
        for successor in self.successors:
            successors.add(successor)
            successors.update(successor.recursive_successors)
        return successors

    @property
    def successor(self) -> "Node | None":
        """Direct successor in the structure graph."""
        if not self.ctx.graph.has_node(self):
            return None
        return next(
            self.ctx.graph.successors(self), None
        )  # pytype: disable=bad-return-type

    @property
    def issues(self) -> Issues:
        """Shortcut to access issues in node."""
        return self.ctx.issues

    def validate_name(self):
        """Validates the name."""
        name = self.name
        if not isinstance(name, str):
            self.add_error(f"The name should be a string. Got: {type(name)}.")
            return
        if not name:
            # This case is already checked for in every node's __post_init__ as `name`
            # is a mandatory parameter for Croissant 0.8
            return
        # For Croissant >= 1.0 compliant datasets, we don't enforce any more constraints
        # on names.
        if not self.ctx.is_v0():
            return
        if len(name) > _MAX_NAME_LENGTH:
            self.add_error(
                f'The name "{name}" is too long (>{_MAX_NAME_LENGTH} characters).'
            )
        regex = re.compile(rf"^{NAME_REGEX}$")
        if not regex.match(name):
            self.add_error(f'The name "{name}" contains forbidden characters.')

    def there_exists_at_least_one_property(self, possible_properties: list[str]):
        """Checks for the existence of one of `possible_properties` in `keys`."""
        for possible_property in possible_properties:
            if getattr(self, possible_property, None) is not None:
                return True
        return False

    def __hash__(self):
        """Re-uses parent's hash function (i.e., object)."""
        return super().__hash__()

    def __eq__(self, other: Any) -> bool:
        """Compares two Nodes given their arguments."""
        if isinstance(other, Node):
            return self.uuid == other.uuid
        return False

    def __deepcopy__(self, memo):
        """Overwrites [`copy.deepcopy`](https://docs.python.org/3/library/copy.html).

        This is required to use `copy.deepcopy(metadata)` as needed by e.g. PyTorch
        DataPipes. It is unsure what the full consequences are. So we'll keep
        investigating on a better approach in
        https://github.com/mlcommons/croissant/issues/531.
        """
        kwargs = {}
        for field in dataclasses.fields(self.__class__):
            if field.name in self.__dict__:
                kwargs[field.name] = self.__dict__[field.name]
        # We properly selected the correct kwargs:
        copy = self.__class__(**kwargs)  # pytype: disable=not-instantiable
        memo[id(self)] = copy
        return copy

    def to_json(self) -> Json:
        """Converts the Python class to JSON."""
        cls = self.__class__
        jsonld_type = cls._jsonld_type(self.ctx)
        # IDs that are generated by RDFLib are not kept
        id_by_rdflib = self.id and self.id.startswith("_:")
        jsonld = {
            "@type": self.ctx.rdf.shorten_value(jsonld_type) if jsonld_type else None,
            "@id": None if self.ctx.is_v0() or id_by_rdflib else self.id,
        }
        for field in mlc_dataclasses.jsonld_fields(self):
            url = field.call_url(self.ctx)
            key = self.ctx.rdf.shorten_key(url)
            value = getattr(self, field.name)
            if field.to_jsonld:
                # We explicitly set `to_jsonld`, so use it:
                value = field.call_to_jsonld(self.ctx, value)
            else:
                if isinstance(value, list):
                    value = [_value_to_jsonld(v) for v in value]
                else:
                    value = _value_to_jsonld(value)
            # fields in _LIST_FIELDS are always lists, so we don't unbox them.
            if field.cardinality == "MANY" and field.name not in _LIST_FIELDS:
                value = unbox_singleton_list(value)
            jsonld[key] = value
        jsonld = remove_empty_values(jsonld)
        return sort_dict(jsonld)

    @classmethod
    def from_jsonld(cls, ctx: Context, jsonld: Json):
        """Creates a Python class from JSON-LD."""
        if not isinstance(jsonld, list) and not isinstance(jsonld, dict):
            name = cls._jsonld_type(ctx) or cls.__name__
            ctx.issues.add_error(f'{name} should be a dict with keys. Got "{jsonld}"')
            return None
        if cls._jsonld_type(ctx) == constants.SCHEMA_ORG_DATASET:
            # For `Metadata` node, insert conforms_to/is_live_dataset in the context:
            ctx.conforms_to = CroissantVersion.from_jsonld(
                ctx, jsonld.get(constants.DCTERMS_CONFORMS_TO)
            )
            ctx.is_live_dataset = jsonld.get(constants.ML_COMMONS_IS_LIVE_DATASET(ctx))
        if isinstance(jsonld, list):
            return [cls.from_jsonld(ctx, el) for el in jsonld]
        check_expected_type(ctx.issues, jsonld, cls._jsonld_type(ctx))
        kwargs = {}
        for field in mlc_dataclasses.jsonld_fields(cls):
            url = field.call_url(ctx)
            value = jsonld.get(url)
            if field.from_jsonld:
                # We explicitly set `from_jsonld`, so use it:
                value = field.call_from_jsonld(ctx, value)
            else:
                # We can infer `from_jsonld` from the input_types:
                if isinstance(value, list):
                    value = [_value_from_input_types(ctx, v, field) for v in value]
                    value = list(filter(lambda v: v != dataclasses.MISSING, value))
                else:
                    value = _value_from_input_types(ctx, value, field)
            if field.cardinality == "MANY" and value:
                value = box_singleton_list(value) if value else []
            elif field.cardinality == "ONE" and isinstance(value, list):
                value = value[0] if value else None
                warning = f"`{field.name}` has cardinality `ONE`, but got a list"
                ctx.issues.add_warning(warning)
            if value is not None:
                kwargs[field.name] = value
        return cls(
            ctx=ctx,
            id=uuid_from_jsonld(jsonld),
            jsonld=jsonld,
            **kwargs,
        )

    JSONLD_TYPE: Callable[[Context], term.URIRef] | term.URIRef | str | None = (
        _MISSING_JSONLD_TYPE
    )

    @classmethod
    def _jsonld_type(cls, ctx: Context):
        """Get the actual JSON-LD type according the the ctx."""
        if cls.JSONLD_TYPE == _MISSING_JSONLD_TYPE:
            raise NotImplementedError("Output the right JSON-LD type.")
        elif callable(cls.JSONLD_TYPE):
            return cls.JSONLD_TYPE(ctx)
        else:
            return cls.JSONLD_TYPE


def _value_to_jsonld(value: Any) -> Any:
    """Applies `to_json` to Nodes."""
    if isinstance(value, Node):
        return value.to_json()
    else:
        return value


def _value_from_input_types(
    ctx: Context, value: Any, field: mlc_dataclasses.JsonldField
) -> Any:
    """Retrieves the value based on the JsonldField."""
    if value is None:
        return None
    input_types = field.input_types
    if not input_types:
        # This is a problem in mlcroissant, so we raise an error:
        raise ValueError(f"`{field.name}` doesn't declare any `input_types`.")
    for input_type in input_types:
        # Either the input_type is a Node...
        if isinstance(value, dict) and _is_a_node(input_type):
            jsonld_type = input_type._jsonld_type(ctx)
            actual_jsonld_type = value.get("@type")
            if actual_jsonld_type == jsonld_type:
                return input_type.from_jsonld(ctx, value)
        # ...or it's a basic int/str/bool/etc type
        else:
            matching_type = MATCHING_TYPES.get(input_type)
            if type(value) is matching_type:
                return value
    types = [
        input_type._jsonld_type(ctx) if _is_a_node(input_type) else str(input_type)
        for input_type in input_types
    ]
    if isinstance(value, dict):
        actual_jsonld_type = value.get("@type")
        posible_attributes = " or ".join([f'"@type": "{type}"' for type in types])
        if ctx.is_v0():
            uuid = value.get(constants.SCHEMA_ORG_NAME)
        else:
            uuid = uuid_from_jsonld(value)
        ctx.issues.add_error(
            f'"{uuid}" should have an attribute {posible_attributes}. Got'
            f" {actual_jsonld_type} instead."
        )
    else:
        actual_type = type(value).__name__
        ctx.issues.add_error(
            f"`{field.name}` should have type {' or '.join(types)}, but got"
            f" {actual_type}"
        )
    if field.default != dataclasses.MISSING:
        # If the validation failed, we return the default value:
        return field.default
    elif field.default_factory != dataclasses.MISSING:
        # For lists, we don't return field.default_factory() to not produce [[]]:
        return dataclasses.MISSING
    raise ValueError(f"{field.name} specifies neither default, nor default_factory")


def _is_a_node(input_type: Any) -> bool:
    return inspect.isclass(input_type) and issubclass(input_type, Node)


def node_by_uuid(ctx: Context, uuid: str | None) -> Node | None:
    """Retrieves a node in the graph by its UID."""
    for node in ctx.graph.nodes():
        if node.uuid == uuid:  # pytype: disable=attribute-error
            return node  # pytype: disable=bad-return-type
    return None
