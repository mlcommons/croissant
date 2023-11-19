import streamlit as st

from core.past_projects import add_new_project
from core.state import CurrentStep
from core.state import Metadata
from utils import set_form_step
from views.load import render_load
from views.previous_files import render_previous_files
from views.side_buttons import set_form_step


def render_splash():
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        with st.expander("**Load an existing Croissant JSON-LD file**", expanded=True):
            render_load()
        with st.expander("**Create from scratch**", expanded=True):

            def create_new_croissant():
                new_meta = Metadata()
                st.session_state[Metadata] = new_meta
                add_new_project(new_meta)
                set_form_step("Jump", CurrentStep.editor)

            st.button(
                "Create",
                on_click=create_new_croissant,
                type="primary",
            )
    with col2:
        with st.expander("**Past projects**", expanded=True):
            render_previous_files()
