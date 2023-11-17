"""Streamlit session state.

In the future, this could be the serialization format between front and back.
"""

from __future__ import annotations

import dataclasses

import pandas as pd

import mlcroissant as mlc


class CurrentStep:
    """Holds all major state variables for the application."""

    splash = "splash"
    editor = "editor"


class SelectedResource:
    """The selected FileSet or FileObject on the `Resources` page."""

    pass


@dataclasses.dataclass
class SelectedRecordSet:
    """The selected RecordSet on the `RecordSets` page."""

    record_set_key: int
    record_set: RecordSet


@dataclasses.dataclass
class FileObject:
    """FileObject analogue for editor"""

    name: str | None = None
    description: str | None = None
    contained_in: list[str] | None = dataclasses.field(default_factory=list)
    content_size: str | None = None
    content_url: str | None = None
    encoding_format: str | None = None
    sha256: str | None = None
    df: pd.DataFrame | None = None
    rdf: mlc.Rdf = dataclasses.field(default_factory=mlc.Rdf)


@dataclasses.dataclass
class FileSet:
    """FileSet analogue for editor"""

    contained_in: list[str] = dataclasses.field(default_factory=list)
    description: str | None = None
    encoding_format: str | None = ""
    includes: str | None = ""
    name: str = ""
    rdf: mlc.Rdf = dataclasses.field(default_factory=mlc.Rdf)


@dataclasses.dataclass
class Field:
    """Field analogue for editor"""

    name: str | None = None
    description: str | None = None
    data_types: str | list[str] | None = None
    source: mlc.Source | None = None
    rdf: mlc.Rdf = dataclasses.field(default_factory=mlc.Rdf)
    references: mlc.Source | None = None


@dataclasses.dataclass
class RecordSet:
    """Record Set analogue for editor"""

    name: str = ""
    description: str | None = None
    is_enumeration: bool | None = None
    key: str | list[str] | None = None
    fields: list[Field] = dataclasses.field(default_factory=list)
    rdf: mlc.Rdf = dataclasses.field(default_factory=mlc.Rdf)


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
    rdf: mlc.Rdf = dataclasses.field(default_factory=mlc.Rdf)

    def __bool__(self):
        return self.name != "" and self.url != ""

    def rename_distribution(self, old_name: str, new_name: str):
        """Renames a resource by changing all the references to this resource."""
        # Update other resources:
        for i, resource in enumerate(self.distribution):
            contained_in = resource.contained_in
            if contained_in and old_name in contained_in:
                self.distribution[i].contained_in = [
                    new_name if name == old_name else name for name in contained_in
                ]
        # Updating source/references works just as with RecordSets.
        self.rename_record_set(old_name, new_name)

    def rename_record_set(self, old_name: str, new_name: str):
        """Renames a RecordSet by changing all the references to this RecordSet."""
        for i, record_set in enumerate(self.record_sets):
            for j, field in enumerate(record_set.fields):
                # Update source
                source = field.source
                if source and source.uid and source.uid.startswith(old_name):
                    new_uid = source.uid.replace(old_name, new_name, 1)
                    self.record_sets[i].fields[j].source.uid = new_uid
                # Update references
                references = field.references
                if (
                    references
                    and references.uid
                    and references.uid.startswith(old_name)
                ):
                    new_uid = references.uid.replace(old_name, new_name, 1)
                    self.record_sets[i].fields[j].references.uid = new_uid

    def rename_field(self, old_name: str, new_name: str):
        """Renames a field by changing all the references to this field."""
        for i, record_set in enumerate(self.record_sets):
            for j, field in enumerate(record_set.fields):
                # Update source
                source = field.source
                # The difference with RecordSet is the `.endswith` here:
                if (
                    source
                    and source.uid
                    and "/" in source.uid
                    and source.uid.endswith(old_name)
                ):
                    new_uid = source.uid.replace(old_name, new_name, 1)
                    self.record_sets[i].fields[j].source.uid = new_uid
                # Update references
                references = field.references
                if (
                    references
                    and references.uid
                    and "/" in references.uid
                    and references.uid.endswith(old_name)
                ):
                    new_uid = references.uid.replace(old_name, new_name, 1)
                    self.record_sets[i].fields[j].references.uid = new_uid

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
        old_name = self.distribution[key].name
        new_name = distribution.name
        if old_name != new_name:
            self.rename_distribution(old_name=old_name, new_name=new_name)
        self.distribution[key] = distribution

    def remove_distribution(self, key: int) -> None:
        del self.distribution[key]

    def add_record_set(self, record_set: RecordSet) -> None:
        self.record_sets.append(record_set)

    def update_record_set(self, key: int, record_set: RecordSet) -> None:
        old_name = self.record_sets[key].name
        new_name = record_set.name
        if old_name != new_name:
            self.rename_record_set(old_name=old_name, new_name=new_name)
        self.record_sets[key] = record_set

    def remove_record_set(self, key: int) -> None:
        del self.record_sets[key]

    def _find_record_set(self, record_set_key: int) -> RecordSet:
        if record_set_key >= len(self.record_sets):
            raise ValueError(f"Wrong index when finding a RecordSet: {record_set_key}")
        return self.record_sets[record_set_key]

    def add_field(self, record_set_key: int, field: Field) -> None:
        record_set = self._find_record_set(record_set_key)
        record_set.fields.append(field)
        self.update_record_set(record_set_key, record_set)

    def update_field(
        self, record_set_key: int, field_key: int, field: RecordSet
    ) -> None:
        record_set = self._find_record_set(record_set_key)
        if field_key >= len(record_set.fields):
            raise ValueError(f"Wrong index when updating field: {field_key}")
        old_name = record_set.fields[field_key].name
        new_name = field.name
        if old_name != new_name:
            self.rename_field(old_name=old_name, new_name=new_name)
        record_set.fields[field_key] = field
        self.update_record_set(record_set_key, record_set)

    def remove_field(self, record_set_key: int, field_key: int) -> None:
        record_set = self._find_record_set(record_set_key)
        if field_key >= len(record_set.fields):
            raise ValueError(f"Wrong index when removing field: {field_key}")
        del record_set.fields[field_key]
        self.update_record_set(record_set_key, record_set)

    def to_canonical(self) -> mlc.Metadata:
        distribution = []
        for file in self.distribution:
            if isinstance(file, FileObject):
                distribution.append(
                    mlc.FileObject(
                        name=file.name,
                        description=file.description,
                        contained_in=file.contained_in,
                        content_url=file.content_url,
                        encoding_format=file.encoding_format,
                        content_size=file.content_size,
                        rdf=file.rdf,
                        sha256=file.sha256,
                    )
                )
            elif isinstance(file, FileSet):
                distribution.append(
                    mlc.FileSet(
                        name=file.name,
                        description=file.description,
                        contained_in=file.contained_in,
                        encoding_format=file.encoding_format,
                        rdf=file.rdf,
                    )
                )
        record_sets = []
        for record_set in self.record_sets:
            fields = []
            for field in record_set.fields:
                fields.append(
                    mlc.Field(
                        name=field.name,
                        description=field.description,
                        data_types=field.data_types,
                        source=field.source,
                        rdf=field.rdf,
                        references=field.references,
                    )
                )
            record_sets.append(
                mlc.RecordSet(
                    name=record_set.name,
                    description=record_set.description,
                    key=record_set.key,
                    is_enumeration=record_set.is_enumeration,
                    fields=fields,
                    rdf=record_set.rdf,
                )
            )
        return mlc.Metadata(
            name=self.name,
            citation=self.citation,
            license=self.license,
            description=self.description,
            url=self.url,
            distribution=distribution,
            rdf=self.rdf,
            record_sets=record_sets,
        )

    @classmethod
    def from_canonical(cls, canonical_metadata: mlc.Metadata) -> Metadata:
        distribution = []
        for file in canonical_metadata.distribution:
            if isinstance(file, mlc.FileObject):
                distribution.append(
                    FileObject(
                        name=file.name,
                        contained_in=file.contained_in,
                        description=file.description,
                        content_size=file.content_size,
                        encoding_format=file.encoding_format,
                        content_url=file.content_url,
                        rdf=file.rdf,
                        sha256=file.sha256,
                    )
                )
            else:
                distribution.append(
                    FileSet(
                        name=file.name,
                        contained_in=file.contained_in,
                        description=file.description,
                        encoding_format=file.encoding_format,
                        rdf=file.rdf,
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
                        data_types=field.data_types,
                        source=field.source,
                        rdf=field.rdf,
                        references=field.references,
                    )
                )
            record_sets.append(
                RecordSet(
                    name=record_set.name,
                    description=record_set.description,
                    is_enumeration=record_set.is_enumeration,
                    key=record_set.key,
                    fields=fields,
                    rdf=record_set.rdf,
                )
            )
        return cls(
            name=canonical_metadata.name,
            description=canonical_metadata.description,
            citation=canonical_metadata.citation,
            license=canonical_metadata.license,
            url=canonical_metadata.url,
            distribution=distribution,
            rdf=canonical_metadata.rdf,
            record_sets=record_sets,
        )
