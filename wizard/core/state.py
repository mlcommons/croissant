"""Streamlit session state.

In the future, this could be the serialization format between front and back.
"""

from __future__ import annotations

import dataclasses

import pandas as pd

import mlcroissant as mlc


class CurrentStep:
    """hold all major state variables for the application"""

    start = "start"
    load = "load"
    editor = "editor"


@dataclasses.dataclass
class FileObject:
    """FileObject analogue for editor"""

    name: str | None = None
    description: str | None = None
    content_size: str | None = None
    content_url: str | None = None
    encoding_format: str | None = None
    sha256: str | None = None
    df: str | None = None


@dataclasses.dataclass
class FileSet:
    """FileSet analogue for editor"""

    contained_in: list[str] = dataclasses.field(default_factory=list)
    description: str | None = None
    encoding_format: str | None = ""
    includes: str | None = ""
    name: str = ""


@dataclasses.dataclass
class Field:
    """Field analogue for editor"""

    name: str | None = None
    description: str | None = None
    data_types: str | list[str] | None = None
    source: mlc.nodes.Source | None = None


@dataclasses.dataclass
class RecordSet:
    """Record Set analogue for editor"""

    name: str = ""
    description: str | None = None
    is_enumeration: bool | None = None
    key: str | list[str] | None = None
    fields: list[Field] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Metadata:
    """main croissant data object, helper functions exist to load and unload this into the mlcroissant version"""

    name: str = ""
    description: str | None = None
    citation: str | None = None
    license: str | None = ""
    url: str = ""
    distribution: list[FileObject | FileSet] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)

    def __bool__(self):
        return self.name != "" and self.url != ""

    def update_metadata(
        self,
        description: str,
        citation: str,
        license: license,
        url: str = "",
        name: str = "",
    ) -> None:
        self.name = name
        self.description = description
        self.citation = citation
        self.license = license
        self.url = url

    def add_distribution(self, distribution: FileSet | FileObject) -> None:
        self.distribution.append(distribution)

    def update_distribution(self, key: int, distribution: FileSet | FileObject) -> None:
        self.distribution[key] = distribution

    def remove_distribution(self, key: int) -> None:
        del self.distribution[key]

    def add_record_set(self, record_set: RecordSet) -> None:
        self.record_sets.append(record_set)

    def update_record_set(self, key: int, record_set: RecordSet) -> None:
        self.record_sets[key] = record_set

    def remove_record_set(self, key: int) -> None:
        del self.record_sets[key]

    def to_canonical(self) -> mlc.Metadata:
        distribution = []
        for file in self.distribution:
            distribution.append(
                mlc.nodes.FileObject(
                    name=file.name,
                    description=file.description,
                    content_url=file.content_url,
                    encoding_format=file.encoding_format,
                    content_size=file.content_size,
                    sha256=file.sha256,
                )
            )
        record_sets = []
        for record_set in self.record_sets:
            fields = []
            for field in record_set.fields:
                fields.append(
                    mlc.nodes.Field(
                        name=field.name,
                        description=field.description,
                        data_types=field.data_types,
                        source=field.source,
                    )
                )
            record_sets.append(
                mlc.nodes.RecordSet(
                    name=record_set.name,
                    description=record_set.description,
                    key=record_set.key,
                    is_enumeration=record_set.is_enumeration,
                    fields=fields,
                )
            )
        return mlc.nodes.Metadata(
            name=self.name,
            citation=self.citation,
            license=self.license,
            description=self.description,
            url=self.url,
            distribution=distribution,
            record_sets=record_sets,
        )

    @classmethod
    def from_canonical(cls, canonical_metadata: mlc.nodes.Metadata) -> Metadata:
        distribution = []
        for file in canonical_metadata.distribution:
            if isinstance(file, mlc.FileObject):
                distribution.append(
                    FileObject(
                        name=file.name,
                        description=file.description,
                        content_size=file.content_size,
                        encoding_format=file.encoding_format,
                        content_url=file.content_url,
                        sha256=file.sha256,
                    )
                )
            else:
                distribution.append(
                    FileSet(
                        name=file.name,
                        description=file.description,
                        encoding_format=file.encoding_format,
                    )
                )
        record_sets = []
        for record_set in canonical_metadata.record_sets:
            fields = []
            for field in record_set.fields:
                fields.append(
                    Field(
                        name=field.name,
                        description=field.description,
                        data_type=field.data_types,
                        source=field.source,
                    )
                )
            record_sets.append(
                RecordSet(
                    name=record_set.name,
                    description=record_set.description,
                    is_enumeration=record_set.is_enumeration,
                    key=record_set.key,
                    fields=fields,
                )
            )
        return cls(
            name=canonical_metadata.name,
            description=canonical_metadata.description,
            citation=canonical_metadata.citation,
            license=canonical_metadata.license,
            url=canonical_metadata.url,
            distribution=distribution,
            record_sets=record_sets,
        )
