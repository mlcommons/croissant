"""FileSet module."""

from __future__ import annotations

import dataclasses

from etils import epath

from mlcroissant._src.core import constants
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.rdf import Rdf


@dataclasses.dataclass(eq=False, repr=False)
class FileSet(Node):
    """Nodes to describe a dataset FileSet (distribution)."""

    contained_in: list[str] = dataclasses.field(default_factory=list)
    description: str | None = None
    encoding_format: str | None = ""
    includes: str | None = ""
    name: str = ""

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("includes", "encoding_format", "name")

    def to_json(self) -> Json:
        """Converts the `FileSet` to JSON."""
        if isinstance(self.contained_in, list) and len(self.contained_in) == 1:
            contained_in: str | list[str] = self.contained_in[0]
        else:
            contained_in = self.contained_in
        return remove_empty_values({
            "@type": "sc:FileSet",
            "name": self.name,
            "description": self.description,
            "containedIn": contained_in,
            "encodingFormat": self.encoding_format,
            "includes": self.includes,
        })

    @classmethod
    def from_jsonld(
        cls,
        issues: Issues,
        context: Context,
        folder: epath.Path,
        rdf: Rdf,
        file_set: Json,
    ) -> FileSet:
        """Creates a `FileSet` from JSON-LD."""
        check_expected_type(issues, file_set, constants.SCHEMA_ORG_FILE_SET)
        name = file_set.get(constants.SCHEMA_ORG_NAME, "")
        contained_in = file_set.get(constants.SCHEMA_ORG_CONTAINED_IN)
        if contained_in is not None and not isinstance(contained_in, list):
            contained_in = [contained_in]
        return cls(
            issues=issues,
            context=Context(dataset_name=context.dataset_name, distribution_name=name),
            folder=folder,
            contained_in=contained_in,
            description=file_set.get(constants.SCHEMA_ORG_DESCRIPTION),
            encoding_format=file_set.get(constants.SCHEMA_ORG_ENCODING_FORMAT),
            includes=file_set.get(constants.ML_COMMONS_INCLUDES),
            name=name,
            rdf=rdf,
        )
