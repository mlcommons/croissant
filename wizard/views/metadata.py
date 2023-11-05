from state import CurrentStep
from state import Metadata
import streamlit as st
from utils import needed_field

# List from https://www.kaggle.com/discussions/general/116302.
licenses = [
    "Other",
    "Public Domain",
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


def render_metadata():
    name = st.text_input(
        label=needed_field("Name"),
        value=st.session_state[Metadata].name,
        placeholder="Dataset",
    )
    description = st.text_area(
        label="Description",
        value=st.session_state[Metadata].description,
        placeholder="Provide a clear description of the dataset.",
    )
    try:
        index = licenses.index(st.session_state[Metadata].license)
    except ValueError:
        index = None
    license = st.selectbox(
        label="License",
        options=licenses,
        index=index,
    )
    url = st.text_input(
        label=needed_field("URL"),
        value=st.session_state[Metadata].url,
        placeholder="URL to the dataset.",
    )
    citation = st.text_area(
        label="Citation",
        value=st.session_state[Metadata].citation,
        placeholder="@book{\n  title={Title}\n}",
    )
    # We fully recreate the session state in order to force the re-rendering.
    del st.session_state[Metadata]
    st.session_state[Metadata] = Metadata(
        name=name,
        description=description,
        citation=citation,
        license=license,
        url=url,
    )
