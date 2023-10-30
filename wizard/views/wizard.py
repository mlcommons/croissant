from state import CurrentStep
from views.side_buttons import set_form_step
from components.files import render_files
from components.metadata import render_metadata
from components.record_sets import render_record_sets
import streamlit as st


def render_wizard():
    with st.container():
        if st.session_state[CurrentStep] == "metadata" or st.session_state[CurrentStep] == "start":
            render_metadata()
        elif st.session_state[CurrentStep] == "files":
            render_files()
        elif st.session_state[CurrentStep] == "recordsets":
            render_record_sets()
