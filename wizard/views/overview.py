import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
from utils import set_form_step


def render_overview():
    meta = st.session_state[Metadata]
    st.subheader("Name:")
    st.text(meta.name)
    st.subheader("Description:")
    st.text(meta.description)
    st.subheader(f"{len(meta.distribution)} Files")
    st.subheader(f"{len(meta.record_sets)} Record Sets")
