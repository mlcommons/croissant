from state import Croissant
from state import Metadata
import streamlit as st

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
    metadata = st.session_state[Croissant].metadata
    name = st.text_input(
        label=needed_field("Name"),
        value=metadata.name,
        placeholder="Dataset",
    )
    description = st.text_area(
        label="Description",
        value=metadata.description,
        placeholder="Provide a clear description of the dataset.",
    )
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
    st.session_state[Croissant].update_metadata(Metadata(
        name=name,
        description=description,
        license=license,
        url=url,
        citation=citation
    ))
