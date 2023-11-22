import enum

import streamlit as st

from core.state import Metadata
from utils import needed_field

# List from https://www.kaggle.com/discussions/general/116302.
licenses = [
    "Other",
    "Public Domain",
    "Public",
    "CC-0",
    "PDDL",
    "CC-BY",
    "CDLA-Permissive-1.0",
    "ODC-BY",
    "CC-BY-SA",
    "CDLA-Sharing-1.0",
    "ODC-ODbL",
    "CC BY-NC",
    "CC BY-ND",
    "CC BY-NC-SA",
    "CC BY-NC-ND",
]


class MetadataEvent(enum.Enum):
    """Event that triggers a metadata change."""

    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    URL = "URL"
    LICENSE = "LICENSE"
    CITATION = "CITATION"


def handle_metadata_change(event: MetadataEvent, metadata: Metadata, key: str):
    if event == MetadataEvent.NAME:
        metadata.name = st.session_state[key]
    elif event == MetadataEvent.DESCRIPTION:
        metadata.description = st.session_state[key]
    elif event == MetadataEvent.LICENSE:
        metadata.license = st.session_state[key]
    elif event == MetadataEvent.CITATION:
        metadata.citation = st.session_state[key]
    elif event == MetadataEvent.URL:
        metadata.url = st.session_state[key]


def render_metadata():
    metadata = st.session_state[Metadata]
    try:
        index = licenses.index(metadata.license)
    except ValueError:
        index = None
    key = "metadata-license"
    st.selectbox(
        label="License",
        key=key,
        options=licenses,
        index=index,
        on_change=handle_metadata_change,
        args=(MetadataEvent.LICENSE, metadata, key),
    )
    key = "metadata-citation"
    st.text_area(
        label="Citation",
        key=key,
        value=metadata.citation,
        placeholder="@book{\n  title={Title}\n}",
        on_change=handle_metadata_change,
        args=(MetadataEvent.CITATION, metadata, key),
    )
