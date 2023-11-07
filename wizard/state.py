"""Streamlit session state.

In the future, this could be the serialization format between front and back.
"""

import dataclasses
from typing import List

import streamlit as st

import mlcroissant as mlc


def init_state():

    if Croissant not in st.session_state:
        st.session_state[Croissant] = Croissant()

    if mlc.Dataset not in st.session_state:
        st.session_state[mlc.Dataset] = None

    if CurrentStep not in st.session_state:
        st.session_state[CurrentStep] = "start"


class CurrentStep:
    pass

@dataclasses.dataclass
class Distribution:
    name: str | None = None
    description: str | None = None
    content_size: str | None = None
    content_url: str | None = None
    encoding_format: str | None = None
    sha256: str | None = None
    df: str | None = None

@dataclasses.dataclass
class Field:
    name: str | None = None
    description: str | None = None
    data_type: str | None = None

@dataclasses.dataclass
class RecordSet:
    name: str = ""
    description: str | None = None
    is_enumeration: bool | None = None
    key: str | list[str] | None = None
    fields: list[Field] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class Metadata:
    name: str = ""
    description: str | None = None
    citation: str | None = None
    license: str | None = ""
    url: str = ""

    def __bool__(self):
        return self.name != "" and self.url != ""
    
@dataclasses.dataclass
class Croissant:
    metadata: Metadata = Metadata()
    distributions: list[Distribution] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)
    def update_metadata(self, metadata: Metadata) -> None:
        self.metadata = Metadata
    def add_distribution(self, distribution: Distribution) -> None:
        self.distributions.append(distribution)
    def update_distribution(self, key: int, distribution: Distribution) -> None:
        self.distributions[key] = distribution
    def remove_distribution(self, key: int) -> None:
        del self.distributions[key]
    def add_record_set(self, record_set: RecordSet) -> None:
        self.record_sets.append(record_set)
    def update_record_set(self, key: int, record_set: RecordSet) -> None:
        self.record_sets[key] = record_set
    def remove_record_set(self, key: int) -> None:
        del self.record_sets[key]

def CanonicalToWizard(dataset: mlc.Dataset) -> Croissant:
    canonical_metadata = dataset.metadata
    metadata = Metadata(
        name=canonical_metadata.name,
        description=canonical_metadata.description,
        citation=canonical_metadata.citation,
        license=canonical_metadata.license,
        url=canonical_metadata.url
    )
    distributions = []
    for file in canonical_metadata.distribution:
        if isinstance(file, mlc.nodes.FileObject):
            distributions.append(Distribution(
                name=file.name,
                description=file.description,
                content_size=file.content_size,
                encoding_format=file.encoding_format,
                sha256=file.sha256,
            ))
        else:
            distributions.append(Distribution(
                name=file.name,
                description=file.description,
                encoding_format=file.encoding_format,
            ))
    record_sets = []
    for record_set in canonical_metadata.record_sets:
        fields = []
        for field in record_set.fields:
            fields.append(Field(
                name=field.name,
                description=field.description,
                data_type=field.data_types
            )) 
        record_sets.append(RecordSet(
            name=record_set.name,
            description=record_set.description,
            is_enumeration=record_set.is_enumeration,
            key=record_set.key,
            fields=fields
        ))
    return Croissant(
        metadata=metadata,
        distributions=distributions,
        record_sets=record_sets
    )

def set_form_step(action, step=None):
    """Maintains the user's location within the wizard."""
    if action == "Jump" and step is not None:
        st.session_state[CurrentStep] = step
