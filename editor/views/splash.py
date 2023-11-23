import streamlit as st

from core.constants import OAUTH_CLIENT_ID
from core.state import CurrentProject
from core.state import CurrentStep
from core.state import Metadata
from utils import jump_to
from views.load import render_load
from views.previous_files import render_previous_files
from views.side_buttons import jump_to


def render_splash():
    if OAUTH_CLIENT_ID:
        st.write(
            "**Disclaimer**: Do not put sensitive information or datasets here. If you"
            " want to host your own version locally, build the app from [the GitHub"
            " repository](https://github.com/mlcommons/croissant/tree/main/editor)."
        )
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        with st.expander("**Load an existing Croissant JSON-LD file**", expanded=True):
            render_load()
        with st.expander("**Create from scratch**", expanded=True):

            def create_new_croissant():
                st.session_state[Metadata] = Metadata()
                st.session_state[CurrentProject] = CurrentProject.create_new()
                jump_to(CurrentStep.editor)

            st.button(
                "Create",
                on_click=create_new_croissant,
                type="primary",
            )
    with col2:
        with st.expander("**Past projects**", expanded=True):
            render_previous_files()
