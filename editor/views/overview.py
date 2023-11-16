import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
from utils import needed_field
from utils import set_form_step


def render_overview():
    metadata = st.session_state[Metadata]
    name = st.text_input(
        label=needed_field("Name"),
        value=metadata.name,
        placeholder="Dataset",
        key="metadata_name",
    )
    description = st.text_area(
        label="Description",
        value=metadata.description,
        placeholder="Provide a clear description of the dataset.",
        key="metadata_description",
    )
    st.subheader(f"{len(metadata.distribution)} Resources")
    st.subheader(f"{len(metadata.record_sets)} Record Sets")
