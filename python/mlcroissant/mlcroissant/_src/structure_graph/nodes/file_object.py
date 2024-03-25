"""FileObject module."""

from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.constants import ML_COMMONS
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source


@mlc_dataclasses.dataclass
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

    content_url: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description=(
            "Actual bytes of the media object, for example the image file or video"
            " file."
        ),
        input_types=[SDO.URL],
        url=SDO.contentUrl,
    )
    content_size: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description=(
            "File size in (mega/kilo/...)bytes. Defaults to bytes if a unit is not"
            " specified."
        ),
        input_types=[SDO.Text],
        url=SDO.contentSize,
    )
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
    md5: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=lambda ctx: ML_COMMONS(ctx).md5,
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
    same_as: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description=(
            "URL (or local name) of a FileObject with the same content, but in a"
            " different format."
        ),
        input_types=[SDO.URL],
        url=SDO.sameAs,
    )
    sha256: str | None = mlc_dataclasses.jsonld_field(
        cardinality="ONE",
        default=None,
        description="Checksum for the file contents.",
        input_types=[SDO.Text],
        url=SDO.sha256,
    )
    source: Source = mlc_dataclasses.jsonld_field(
        default_factory=Source,
        input_types=[Source],
        url=lambda ctx: ML_COMMONS(ctx).source,
    )

    def __post_init__(self):
        """Checks arguments of the node."""
        Node.__post_init__(self)
        self.validate_name()
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.assert_has_mandatory_properties("encoding_format", uuid_field)

        if not self.contained_in:
            self.assert_has_mandatory_properties("content_url")
            if not self.ctx.is_live_dataset:
                self.assert_has_exclusive_properties(["md5", "sha256"])

    JSONLD_TYPE = constants.SCHEMA_ORG_FILE_OBJECT
