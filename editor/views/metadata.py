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


def render_metadata():
    metadata = st.session_state[Metadata]
    try:
        index = licenses.index(metadata.license)
    except ValueError:
        index = None
    license = st.selectbox(
        label="License",
        options=licenses,
        index=index,
    )
    url = st.text_input(
        label=needed_field("URL"),
        value=metadata.url,
        placeholder="URL to the dataset.",
    )
    citation = st.text_area(
        label="Citation",
        value=metadata.citation,
        placeholder="@book{\n  title={Title}\n}",
    )
    # We fully recreate the session state in order to force the re-rendering.
    st.session_state[Metadata].update_metadata(
        name=metadata.name,
        description=metadata.description,
        license=license,
        url=url,
        citation=citation,
    )
