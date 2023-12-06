import streamlit as st

from core.state import Metadata
from events.metadata import find_license_index
from events.metadata import handle_metadata_change
from events.metadata import LICENSES
from events.metadata import LICENSES_URL
from events.metadata import MetadataEvent


def render_metadata():
    """Renders the `Metadata` view."""
    metadata = st.session_state[Metadata]
    index = find_license_index(metadata.license)
    key = "metadata-url"
    st.text_input(
        label="URL",
        key=key,
        value=metadata.url,
        placeholder="URL to the dataset.",
        on_change=handle_metadata_change,
        args=(MetadataEvent.URL, metadata, key),
    )
    key = "metadata-version"
    st.text_input(
        label="Version (`MAJOR.MINOR.PATCH`)",
        key=key,
        help=(
            "Refer to https://semver.org/spec/v2.0.0.html for more information on the"
            " format."
        ),
        value=metadata.version,
        placeholder="1.0.0",
        on_change=handle_metadata_change,
        args=(MetadataEvent.VERSION, metadata, key),
    )
    key = "metadata-license"
    st.selectbox(
        label="License",
        help=(
            "More information on license names and meaning can be found"
            f" [here]({LICENSES_URL})."
        ),
        key=key,
        options=LICENSES.keys(),
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
