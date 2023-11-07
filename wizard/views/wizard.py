from core.state import CurrentStep
import streamlit as st
from views.files import render_files
from views.metadata import render_metadata
from views.record_sets import render_record_sets


def render_wizard():
    with st.expander("Metadata", expanded=True):
        render_metadata()
    with st.expander("Files"):
        render_files()
    with st.expander("Record Sets"):
        render_record_sets()
