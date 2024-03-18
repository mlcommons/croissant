"""FileSet module."""

from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node


@mlc_dataclasses.dataclass
class FileSet(Node):
    """Nodes to describe a dataset FileSet (distribution)."""

    JSONLD_TYPE = constants.SCHEMA_ORG_FILE_SET

    contained_in: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "Another FileObject or FileSet that this one is contained in, e.g., in the"
            " case of a file extracted from an archive. When this property is present,"
            " the contentUrl is evaluated as a relative path within the container"
            " object"
        ),
        from_jsonld=lambda ctx, contained_in: uuid_from_jsonld(contained_in),
        to_jsonld=lambda ctx, contained_in: [
            formatted_uuid_to_json(ctx, uuid) for uuid in contained_in
        ],
        url=SDO.containedIn,
    )
    description: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=SDO.description,
    )
    encoding_format: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="The format of the file, given as a mime type.",
        input_types=[SDO.Text],
        url=SDO.encodingFormat,
    )
    excludes: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description="A glob pattern that specifies the files to exclude.",
        input_types=[SDO.Text],
        url=lambda ctx: constants.ML_COMMONS_EXCLUDES(ctx),
    )
    includes: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description="A glob pattern that specifies the files to include.",
        input_types=[SDO.Text],
        url=lambda ctx: constants.ML_COMMONS_INCLUDES(ctx),
    )
    name: str = mlc_dataclasses.jsonld_field(
        default="",
        description=(
            "The name of the file.  As much as possible, the name should reflect the"
            " name of the file as downloaded, including the file extension. e.g."
            ' "images.zip".'
        ),
        input_types=[SDO.Text],
        url=SDO.name,
    )

    def __post_init__(self):
        """Checks arguments of the node."""
        Node.__post_init__(self)
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.validate_name()
        self.assert_has_mandatory_properties("includes", "encoding_format", uuid_field)
