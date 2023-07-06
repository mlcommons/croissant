"""FileObject module."""

import dataclasses

from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(frozen=True, repr=False)
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

    content_url: str = ""
    content_size: str = ""
    contained_in: tuple[str] = ()
    description: str | None = None
    encoding_format: str = ""
    md5: str | None = None
    name: str = ""
    sha256: str | None = None
    source: Source | None = None

    def check(self):
        self.assert_has_mandatory_properties("content_url", "encoding_format", "name")
        if not self.contained_in:
            self.assert_has_exclusive_properties(["md5", "sha256"])
