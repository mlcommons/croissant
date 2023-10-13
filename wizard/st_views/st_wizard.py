from st_state import CurrentStep
from st_views.st_side_buttons import set_form_step
from st_views.steps.st_files import render_files
from st_views.steps.st_metadata import render_metadata
from st_views.steps.st_record_sets import render_record_sets
import streamlit as st


def render_wizard():
    tab1, tab2, tab3 = st.tabs(["Metadata", "Files", "Record sets"])

    tab1.subheader("Dataset metadata")
    tab2.subheader("Import files")
    tab3.subheader("Record sets")

    with tab1:
        render_metadata()
    with tab2:
        render_files()
    with tab3:
        render_record_sets()
