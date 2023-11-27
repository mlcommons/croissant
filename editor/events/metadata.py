import enum

import streamlit as st

from core.state import Metadata


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
