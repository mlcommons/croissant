import dataclasses
import enum

import streamlit as st

from core.files import FILE_OBJECT
from core.path import get_resource_path
from core.state import FileObject
from core.state import FileSet
from core.state import Metadata

Resource = FileObject | FileSet


class ResourceEvent(enum.Enum):
    """Event that triggers a resource change."""

    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    ENCODING_FORMAT = "ENCODING_FORMAT"
    INCLUDES = "INCLUDES"
    SHA256 = "SHA256"
    CONTAINED_IN = "CONTAINED_IN"
    CONTENT_SIZE = "CONTENT_SIZE"
    CONTENT_URL = "CONTENT_URL"
    TYPE = "TYPE"


def handle_resource_change(event: ResourceEvent, resource: Resource, key: str):
    value = st.session_state[key]
    if event == ResourceEvent.NAME:
        old_name = resource.name
        new_name = value
        if old_name != new_name:
            metadata: Metadata = st.session_state[Metadata]
            metadata.rename_distribution(old_name=old_name, new_name=new_name)
        resource.name = value
    elif event == ResourceEvent.DESCRIPTION:
        resource.description = value
    elif event == ResourceEvent.ENCODING_FORMAT:
        resource.encoding_format = value
    elif event == ResourceEvent.INCLUDES:
        resource.includes = value
    elif event == ResourceEvent.SHA256:
        resource.sha256 = value
    elif event == ResourceEvent.CONTAINED_IN:
        resource.contained_in = value
    elif event == ResourceEvent.CONTENT_SIZE:
        resource.content_size = value
    elif event == ResourceEvent.CONTENT_URL:
        if resource.content_url and value:
            old_path = get_resource_path(resource.content_url)
            new_path = get_resource_path(value)
            if old_path.exists() and not new_path.exists():
                old_path.rename(new_path)
        resource.content_url = value
    elif event == ResourceEvent.TYPE:
        metadata: Metadata = st.session_state[Metadata]
        index = metadata.distribution.index(resource)
        # Changing type by trying to retain as many attributes as possible.
        if value == FILE_OBJECT:
            file_object = _create_instance1_from_instance2(resource, FileObject)
            metadata.distribution[index] = file_object
        else:
            file_set = _create_instance1_from_instance2(resource, FileSet)
            metadata.distribution[index] = file_set


def _create_instance1_from_instance2(instance1: Resource, instance2: type):
    """Creates instance2 by retaining as many common attributes as possible."""
    attributes1 = set((field.name for field in dataclasses.fields(instance1)))
    attributes2 = set((field.name for field in dataclasses.fields(instance2)))
    common_attributes = attributes2.intersection(attributes1)
    return instance2(**{
        attribute: getattr(instance1, attribute) for attribute in common_attributes
    })
