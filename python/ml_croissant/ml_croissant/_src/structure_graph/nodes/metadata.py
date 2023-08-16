"""Metadata module."""

from __future__ import annotations

import dataclasses
import json

from etils import epath

from ml_croissant._src.core import constants
from ml_croissant._src.core.data_types import check_expected_type
from ml_croissant._src.core.issues import Context
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.core.json_ld import _make_context
from ml_croissant._src.core.json_ld import expand_jsonld
from ml_croissant._src.core.json_ld import remove_empty_values
from ml_croissant._src.core.types import Json
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.file_object import FileObject
from ml_croissant._src.structure_graph.nodes.file_set import FileSet
from ml_croissant._src.structure_graph.nodes.record_set import RecordSet


@dataclasses.dataclass(eq=False, repr=False)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

    citation: str | None = None
    description: str | None = None
    language: str | None = None
    license: str | None = None
    name: str = ""
    url: str = ""
    file_objects: list[FileObject] = dataclasses.field(default_factory=list)
    file_sets: list[FileSet] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("name", "url")
        self.assert_has_optional_properties("citation", "license")

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""
        return remove_empty_values(
            {
                "@context": _make_context(),
                "@language": self.language,
                "@type": "sc:Dataset",
                "name": self.name,
                "description": self.description,
                "citation": self.citation,
                "license": self.license,
                "url": self.url,
                "distribution": [f.to_json() for f in self.distribution],
                "recordSet": [record_set.to_json() for record_set in self.record_sets],
            }
        )

    @property
    def distribution(self) -> list[FileObject | FileSet]:
        """Gets `https://schema.org/distribution`: union of FileSets and FileObjects."""
        return self.file_objects + self.file_sets

    def nodes(self) -> list[Node]:
        """List all nodes in metadata."""
        nodes: list[Node] = [self]
        nodes.extend(self.distribution)
        nodes.extend(self.record_sets)
        for record_set in self.record_sets:
            nodes.extend(record_set.fields)
            for field in record_set.fields:
                nodes.extend(field.sub_fields)
        return nodes

    @classmethod
    def from_json(
        cls,
        json_: str | Json,
    ) -> Metadata:
        """Creates a `Metadata` from JSON."""
        if isinstance(json_, str):
            json_ = json.loads(json_)
        jsonld = expand_jsonld(json_)
        return cls.from_jsonld(issues=Issues(), folder=None, metadata=jsonld)

    @classmethod
    def from_jsonld(
        cls,
        issues: Issues,
        folder: epath.Path,
        metadata: Json,
    ) -> Metadata:
        """Creates a `Metadata` from JSON-LD."""
        check_expected_type(issues, metadata, constants.SCHEMA_ORG_DATASET)
        file_sets: list[FileSet] = []
        file_objects: list[FileObject] = []
        record_sets: list[RecordSet] = []
        distributions = metadata.get(str(constants.SCHEMA_ORG_DISTRIBUTION), [])
        dataset_name = metadata.get(str(constants.SCHEMA_ORG_NAME), "")
        context = Context(dataset_name=dataset_name)
        for distribution in distributions:
            name = distribution.get(str(constants.SCHEMA_ORG_NAME), "")
            distribution_type = distribution.get("@type")
            if distribution_type == str(constants.SCHEMA_ORG_FILE_OBJECT):
                file_objects.append(
                    FileObject.from_jsonld(issues, context, folder, distribution)
                )
            elif distribution_type == str(constants.SCHEMA_ORG_FILE_SET):
                file_sets.append(
                    FileSet.from_jsonld(issues, context, folder, distribution)
                )
            else:
                issues.add_error(
                    f'"{name}" should have an attribute "@type":'
                    f' "{str(constants.SCHEMA_ORG_FILE_OBJECT)}" or "@type":'
                    f' "{str(constants.SCHEMA_ORG_FILE_SET)}". Got'
                    f" {distribution_type} instead."
                )
        record_sets = metadata.get(str(constants.ML_COMMONS_RECORD_SET), [])
        record_sets = [
            RecordSet.from_jsonld(issues, context, folder, record_set)
            for record_set in record_sets
        ]
        new_cls = cls(
            issues=issues,
            context=context,
            folder=folder,
            citation=metadata.get(str(constants.SCHEMA_ORG_CITATION)),
            description=metadata.get(str(constants.SCHEMA_ORG_DESCRIPTION)),
            file_objects=file_objects,
            file_sets=file_sets,
            language=metadata.get(str(constants.SCHEMA_ORG_LANGUAGE)),
            license=metadata.get(str(constants.SCHEMA_ORG_LICENSE)),
            name=dataset_name,
            record_sets=record_sets,
            url=metadata.get(str(constants.SCHEMA_ORG_URL)),
        )
        # Define parents
        for node in new_cls.distribution:
            node.parents = [new_cls]
        for record_set in new_cls.record_sets:
            record_set.parents = [new_cls]
            for field in record_set.fields:
                field.parents = [new_cls, record_set]
                for sub_field in field.sub_fields:
                    sub_field.parents = [new_cls, record_set, field]
        return new_cls
