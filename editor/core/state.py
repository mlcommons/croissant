"""Streamlit session state.

In the future, this could be the serialization format between front and back.
"""

from __future__ import annotations

import base64
import dataclasses
import datetime
from typing import Any

from etils import epath
import pandas as pd
import requests
import streamlit as st

from core.constants import OAUTH_CLIENT_ID
from core.constants import OAUTH_CLIENT_SECRET
from core.constants import PAST_PROJECTS_PATH
from core.constants import PROJECT_FOLDER_PATTERN
from core.constants import REDIRECT_URI
from core.constants import TABS
from core.names import find_unique_name
import mlcroissant as mlc


def create_class(mlc_class: type, instance: Any, **kwargs) -> Any:
    """Creates the mlcroissant class `mlc_class` from the editor `instance`."""
    fields = dataclasses.fields(mlc_class)
    params: dict[str, Any] = {}
    for field in fields:
        name = field.name
        if hasattr(instance, name) and name not in kwargs:
            params[name] = getattr(instance, name)
    if "uuid" in params and params.get("uuid") is None:
        # Let mlcroissant handle the default value
        del params["uuid"]
    return mlc_class(**params, **kwargs)


@dataclasses.dataclass
class User:
    """The connected user."""

    access_token: str
    id_token: str
    username: str

    @classmethod
    def connect(cls, code: str):
        credentials = base64.b64encode(
            f"{OAUTH_CLIENT_ID}:{OAUTH_CLIENT_SECRET}".encode()
        ).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
        }
        data = {
            "client_id": OAUTH_CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        url = "https://huggingface.co/oauth/token"
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            response = response.json()
            access_token = response.get("access_token")
            id_token = response.get("id_token")
            if access_token and id_token:
                url = "https://huggingface.co/oauth/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    response = response.json()
                    username = response.get("preferred_username")
                    if username:
                        return User(
                            access_token=access_token,
                            username=username,
                            id_token=id_token,
                        )
        raise Exception(
            f"Could not connect to Hugging Face. Please, go to {REDIRECT_URI}."
            f" ({response=})."
        )


def get_user():
    """Get user from session_state."""
    return st.session_state.get(User)


@dataclasses.dataclass
class CurrentProject:
    """The selected project."""

    path: epath.Path

    @classmethod
    def create_new(cls) -> CurrentProject | None:
        timestamp = datetime.datetime.now().strftime(PROJECT_FOLDER_PATTERN)
        return cls.from_timestamp(timestamp)

    @classmethod
    def from_timestamp(cls, timestamp: str) -> CurrentProject | None:
        user = get_user()
        if user is None and OAUTH_CLIENT_ID:
            return None
        else:
            path = PAST_PROJECTS_PATH(user)
            return CurrentProject(path=path / timestamp)


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

    ctx: mlc.Context = dataclasses.field(default_factory=mlc.Context)
    name: str | None = None
    description: str | None = None
    contained_in: list[str] | None = dataclasses.field(default_factory=list)
    content_size: str | None = None
    content_url: str | None = None
    encoding_format: str | None = None
    sha256: str | None = None
    df: pd.DataFrame | None = None
    folder: epath.PathLike | None = None
    uuid: str | None = None


@dataclasses.dataclass
class FileSet:
    """FileSet analogue for editor"""

    ctx: mlc.Context = dataclasses.field(default_factory=mlc.Context)
    contained_in: list[str] = dataclasses.field(default_factory=list)
    description: str | None = None
    encoding_format: str | None = ""
    includes: str | None = ""
    name: str = ""
    uuid: str | None = None


@dataclasses.dataclass
class Field:
    """Field analogue for editor"""

    ctx: mlc.Context = dataclasses.field(default_factory=mlc.Context)
    name: str | None = None
    description: str | None = None
    data_types: str | list[str] | None = None
    source: mlc.Source | None = None
    references: mlc.Source | None = None
    uuid: str | None = None


@dataclasses.dataclass
class RecordSet:
    """Record Set analogue for editor"""

    ctx: mlc.Context = dataclasses.field(default_factory=mlc.Context)
    name: str = ""
    data: list[Any] | None = None
    description: str | None = None
    is_enumeration: bool | None = None
    key: str | list[str] | None = None
    fields: list[Field] = dataclasses.field(default_factory=list)
    uuid: str | None = None


@dataclasses.dataclass
class Metadata:
    """main croissant data object, helper functions exist to load and unload this into the mlcroissant version"""

    name: str = ""
    description: str | None = None
    cite_as: str | None = None
    context: dict = dataclasses.field(default_factory=dict)
    creators: list[mlc.PersonOrOrganization] = dataclasses.field(default_factory=list)
    ctx: mlc.Context = dataclasses.field(default_factory=mlc.Context)
    data_biases: str | None = None
    data_collection: str | None = None
    date_published: datetime.datetime | None = None
    license: str | None = ""
    personal_sensitive_information: str | None = None
    sd_license: str | None = ""
    uuid: str | None = None
    url: str = ""
    distribution: list[FileObject | FileSet] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)
    version: str | None = None

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
                possible_uid = f"{old_name}/"
                # Update source
                source = field.source
                if (
                    source
                    and source.uid
                    and (source.uid.startswith(possible_uid) or source.uid == old_name)
                ):
                    new_uid = source.uid.replace(old_name, new_name, 1)
                    self.record_sets[i].fields[j].source.uid = new_uid
                # Update references
                references = field.references
                if (
                    references
                    and references.uid
                    and (
                        references.uid.startswith(possible_uid)
                        or references.uid == old_name
                    )
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

    def add_distribution(self, distribution: FileSet | FileObject) -> None:
        self.distribution.append(distribution)

    def remove_distribution(self, key: int) -> None:
        del self.distribution[key]

    def add_record_set(self, record_set: RecordSet) -> None:
        name = find_unique_name(self.names(), record_set.name)
        record_set.name = name
        self.record_sets.append(record_set)

    def remove_record_set(self, key: int) -> None:
        del self.record_sets[key]

    def _find_record_set(self, record_set_key: int) -> RecordSet:
        if record_set_key >= len(self.record_sets):
            raise ValueError(f"Wrong index when finding a RecordSet: {record_set_key}")
        return self.record_sets[record_set_key]

    def add_field(self, record_set_key: int, field: Field) -> None:
        record_set = self._find_record_set(record_set_key)
        record_set.fields.append(field)

    def remove_field(self, record_set_key: int, field_key: int) -> None:
        record_set = self._find_record_set(record_set_key)
        if field_key >= len(record_set.fields):
            raise ValueError(f"Wrong index when removing field: {field_key}")
        del record_set.fields[field_key]

    def to_canonical(self) -> mlc.Metadata:
        distribution = []
        ctx = self.ctx
        for file in self.distribution:
            if isinstance(file, FileObject):
                distribution.append(create_class(mlc.FileObject, file, ctx=ctx))
            elif isinstance(file, FileSet):
                distribution.append(create_class(mlc.FileSet, file, ctx=ctx))
        record_sets = []
        for record_set in self.record_sets:
            fields = []
            for field in record_set.fields:
                fields.append(create_class(mlc.Field, field, ctx=ctx))
            record_sets.append(
                create_class(mlc.RecordSet, record_set, ctx=ctx, fields=fields)
            )
        return create_class(
            mlc.Metadata,
            self,
            distribution=distribution,
            record_sets=record_sets,
        )

    @classmethod
    def from_canonical(cls, canonical_metadata: mlc.Metadata) -> Metadata:
        distribution = []
        for file in canonical_metadata.distribution:
            if isinstance(file, mlc.FileObject):
                distribution.append(create_class(FileObject, file))
            else:
                distribution.append(create_class(FileSet, file))
        record_sets = []
        for record_set in canonical_metadata.record_sets:
            fields = []
            for field in record_set.fields:
                fields.append(create_class(Field, field))
            record_sets.append(
                create_class(
                    RecordSet,
                    record_set,
                    fields=fields,
                )
            )
        return create_class(
            cls,
            canonical_metadata,
            distribution=distribution,
            record_sets=record_sets,
        )

    def names(self) -> set[str]:
        nodes = self.distribution + self.record_sets
        return set([node.name for node in nodes])


class OpenTab:
    pass


def get_tab():
    tab = st.session_state.get(OpenTab)
    if tab is None:
        return 0
    else:
        return tab


def set_tab(tab: str):
    if tab not in TABS:
        return
    index = TABS.index(tab)
    st.session_state[OpenTab] = index
