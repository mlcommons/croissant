from st_state import CurrentStep
from st_state import Files
from st_state import Metadata
from st_state import RecordSets
from st_views.st_wizard import render_wizard
from st_views.st_preview import render_preview
import streamlit as st

def package_dataset():
    # todo
    return

if CurrentStep not in st.session_state:
    st.session_state[CurrentStep] = 1

if Files not in st.session_state:
    st.session_state[Files] = []

if Metadata not in st.session_state:
    st.session_state[Metadata] = Metadata()

if RecordSets not in st.session_state:
    st.session_state[RecordSets] = []

st.set_page_config(page_title="Croissant Wizard", layout="wide")
st.header("Croissant Wizard")

render_wizard()
render_preview()

# Render footer
footer_cols = st.columns([7, 1])
footer_cols[1].button(
    "Package dataset",
    on_click=package_dataset,
    disabled=not st.session_state[Metadata] and not st.session_state[Files],
    use_container_width=True,
)
