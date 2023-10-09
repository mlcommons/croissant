from st_state import CurrentStep
from st_views.st_side_buttons import set_form_step
from st_views.steps.st_files import render_files
from st_views.steps.st_metadata import render_metadata
from st_views.steps.st_record_sets import render_record_sets
import streamlit as st


def render_wizard():
    with st.container():
        if st.session_state[CurrentStep] == 1:
            render_metadata()
        elif st.session_state[CurrentStep] == 2:
            render_files()
        elif st.session_state[CurrentStep] == 3:
            render_record_sets()

        # Render footer
        footer_cols = st.columns([6, 1, 1])
        footer_cols[1].button(
            "Back",
            on_click=set_form_step,
            args=["Back"],
            disabled=st.session_state[CurrentStep] == 1,
        )
        footer_cols[2].button(
            "Next",
            on_click=set_form_step,
            args=["Next"],
            disabled=st.session_state[CurrentStep] == 3,
        )
