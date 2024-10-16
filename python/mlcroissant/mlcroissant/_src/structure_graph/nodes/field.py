"""Field module."""

from rdflib import term
from rdflib.namespace import SDO
from typing_extensions import Self

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.data_types import data_types_from_jsonld
from mlcroissant._src.core.data_types import data_types_to_jsonld
from mlcroissant._src.core.data_types import EXPECTED_DATA_TYPES
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.base_node import node_by_uuid
from mlcroissant._src.structure_graph.nodes.source import Source


@mlc_dataclasses.dataclass
class ParentField(Node):
    """Class for the `parentField` property."""

    JSONLD_TYPE = None

    references: Source | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[Source],
        url=constants.ML_COMMONS_REFERENCES,
    )
    source: Source | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[Source],
        url=constants.ML_COMMONS_SOURCE,
    )


@mlc_dataclasses.dataclass
class Field(Node):
    """Nodes to describe a dataset Field."""

    JSONLD_TYPE = constants.ML_COMMONS_FIELD_TYPE

    description: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_DESCRIPTION,
    )
    # `data_types` is different than `node.data_type`. See `data_type`'s docstring.
    data_types: list[term.URIRef] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "The data type of the field, identified by the URI of the corresponding"
            " class. It could be either an atomic type (e.g, `sc:Integer`) or a"
            " semantic type (e.g., `sc:GeoLocation`)."
        ),
        from_jsonld=data_types_from_jsonld,
        to_jsonld=data_types_to_jsonld,
        url=constants.ML_COMMONS_DATA_TYPE,
    )
    equivalentProperty: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description=(
            "A property that is equivalent to this Field. Used in the case a dataType"
            " is specified on the RecordSet to map specific fields to specific"
            " properties associated with that dataType."
        ),
        input_types=[SDO.URL],
        url=constants.ML_COMMONS_EQUIVALENT_PROPERTY,
    )
    is_enumeration: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_IS_ENUMERATION,
        versions=[CroissantVersion.V_0_8],
    )
    name: str = mlc_dataclasses.jsonld_field(
        default="",
        description="The name of the Field.",
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_NAME,
    )
    parent_field: ParentField | None = mlc_dataclasses.jsonld_field(
        default=None,
        description=(
            "A special case of `SubField` that should be hidden because it references a"
            " `Field` that already appears in the `RecordSet`."
        ),
        input_types=[ParentField],
        url=constants.ML_COMMONS_PARENT_FIELD,
    )
    references: Source = mlc_dataclasses.jsonld_field(
        default_factory=Source,
        description=(
            "Another `Field` of another `RecordSet` that this field references. This is"
            " the equivalent of a foreign key reference in a relational database."
        ),
        input_types=[Source],
        url=constants.ML_COMMONS_REFERENCES,
    )
    repeated: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="If true, then the Field is a list of values of type dataType.",
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_REPEATED,
    )
    source: Source = mlc_dataclasses.jsonld_field(
        default_factory=Source,
        description=(
            "The data source of the field. This will generally reference a `FileObject`"
            " or `FileSet`'s contents (e.g., a specific column of a table)."
        ),
        input_types=[Source],
        url=constants.ML_COMMONS_SOURCE,
    )
    sub_fields: list[Self] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description="Another `Field` that is nested inside this one.",
        from_jsonld=lambda ctx, fields: Field.from_jsonld(ctx, fields),
        url=constants.ML_COMMONS_SUB_FIELD,
    )

    def __post_init__(self):
        """Checks arguments of the node."""
        Node.__post_init__(self)
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.validate_name()
        self.assert_has_mandatory_properties(uuid_field)
        self.source.check_source(self.add_error)
        self._standardize_data_types()

    def _standardize_data_types(self):
        """Converts data_types to a list of rdflib.URIRef."""
        data_types = self.data_types
        if data_types is None:
            data_types = []
        if not isinstance(data_types, list):
            data_types = [data_types]
        self.data_types = [term.URIRef(data_type) for data_type in data_types]

    @property
    def data_type(self) -> type | term.URIRef | None:
        """Recursively retrieves the actual data type of the node.

        The data_type can be either directly on the node (`data_type`) or on one
        of the parent fields.

        `data_types` may contain semantic meaning, but `data_type` is the actual
        programmatic data type (i.e., bool, str, etc).
        """
        if self.sub_fields:
            return None
        data_types = self.data_types or []
        for data_type in data_types:
            # data_type can be matched to a Python type:
            if data_type in EXPECTED_DATA_TYPES:
                return EXPECTED_DATA_TYPES[term.URIRef(data_type)]
            # data_type is an ML semantic type:
            elif data_type in [
                DataType.IMAGE_OBJECT,
                # For some reasons, pytype cannot infer `Any` on ctx:
                DataType.BOUNDING_BOX,  # pytype: disable=wrong-arg-types
                DataType.AUDIO_OBJECT,
            ]:
                return term.URIRef(data_type)
        # The data_type has to be found on the source:
        source = node_by_uuid(self.ctx, self.source.uuid)
        if not isinstance(source, Field):
            self.add_error(
                "The field does not specify a valid"
                f" {constants.ML_COMMONS_DATA_TYPE(self.ctx)}, neither does any of"
                f" its predecessor. Got: {self.data_types}"
            )
            return None
        return source.data_type

    @property
    def data(self) -> str | None:
        """The data of the parent RecordSet."""
        if hasattr(self.parent, "data"):
            return getattr(self.parent, "data")
        return None
