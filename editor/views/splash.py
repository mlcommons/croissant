import streamlit as st

from core.state import CurrentStep
from utils import set_form_step
from views.load import render_load
from views.side_buttons import set_form_step


def render_splash():
    col1, col2, col3 = st.columns([1, 1, 1], gap="large")
    with col1:
        with st.expander("**Load an existing Croissant JSON-LD file**", expanded=True):
            render_load()
    with col2:
        with st.expander("**Create from scratch**", expanded=True):
            st.button(
                "Create",
                on_click=set_form_step,
                args=["Jump", CurrentStep.editor],
                type="primary",
            )
    with col3:
        with st.expander("**Past projects**", expanded=True):
            st.write("Coming soon: the list of your past projects.")
