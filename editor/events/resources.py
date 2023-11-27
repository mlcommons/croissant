import enum

import streamlit as st

from core.state import FileObject
from core.state import FileSet
from core.state import Metadata

Resource = FileObject | FileSet


class ResourceEvent(enum.Enum):
    """Event that triggers a resource change."""

    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    ENCODING_FORMAT = "ENCODING_FORMAT"
    SHA256 = "SHA256"
    CONTENT_SIZE = "CONTENT_SIZE"
    CONTENT_URL = "CONTENT_URL"


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
    elif event == ResourceEvent.SHA256:
        resource.sha256 = value
    elif event == ResourceEvent.CONTENT_SIZE:
        resource.content_size = value
    elif event == ResourceEvent.CONTENT_URL:
        resource.content_url = value
