from state import CurrentStep
from views.side_buttons import set_form_step
from views.files import render_files
from views.metadata import render_metadata
from views.record_sets import render_record_sets
import streamlit as st


def render_wizard():
    with st.expander("Metadata", expanded=True):
        render_metadata()
    with st.expander("Files"):
        render_files()
    with st.expander("Record Sets"):
        render_record_sets()
