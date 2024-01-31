import streamlit as st

from core.state import Metadata
from events.metadata import find_license_index
from events.metadata import handle_metadata_change
from events.metadata import LICENSES
from events.metadata import LICENSES_URL
from events.metadata import MetadataEvent


def render_rai_metadata():
    """Renders the `Metadata` view."""
    metadata: Metadata = st.session_state[Metadata]
    col1, col2 = st.columns([1, 1])
    with col1.expander("**Responsible AI (RAI) metadata**", expanded=True):
        _render_rai_fields(metadata)
    with col2.expander("Instructions", expanded=True):
        st.info("Instructions to fill up the RAI section", icon="💡")
        


def _render_rai_fields(metadata: Metadata):
    """Renders RAI (Responsible AI) metadata."""
    key = "metadata-data-collection"
    st.text_area(
        label=(
            "**Data collection**. Key stages of the data collection process encourage"
            " its creators to reflect on the process and improves understanding for"
            " users."
        ),
        key=key,
        value=metadata.data_collection,
        on_change=handle_metadata_change,
        args=(MetadataEvent.DATA_COLLECTION, metadata, key),
    )
    key = "metadata-data-biases"
    st.text_area(
        label=(
            "**Data biases**. Involves understanding the potential risks associated"
            " with data usage and to prevent unintended and potentially harmful"
            " consequences that may arise from using models trained on or evaluated"
            " with the respective data."
        ),
        key=key,
        value=metadata.data_biases,
        on_change=handle_metadata_change,
        args=(MetadataEvent.DATA_BIASES, metadata, key),
    )
    key = "metadata-personal-sensitive-information"
    st.text_area(
        label=(
            "**Personal sensitive information**. Personal and sensitive information, if"
            " contained within the dataset, can play an important role in the"
            " mitigation of any risks and the responsible use of the datasets."
        ),
        key=key,
        value=metadata.personal_sensitive_information,
        on_change=handle_metadata_change,
        args=(MetadataEvent.PERSONAL_SENSITIVE_INFORMATION, metadata, key),
    )
    key = "metadata-personal-other"
    st.text_area(
        label=("**Other field**. And the desceiption"),
        key=key,
        value=metadata.other_field,
        on_change=handle_metadata_change,
        args=(MetadataEvent.OTHER_FIELD, metadata, key),
    )


