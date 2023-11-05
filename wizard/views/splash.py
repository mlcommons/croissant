from state import CurrentStep
import streamlit as st
<<<<<<< HEAD
from state import set_form_step
=======
from views.side_buttons import set_form_step
>>>>>>> main


def render_splash():
    st.text("Welcome to the Croissant Wizard, would you like to load an existing croissant file, or create a new one?")
    col1, col2, col3 = st.columns([1,1,8], gap="small")
    with col1:
        st.button(
            "Load",
            on_click=set_form_step,
            args=["Jump", CurrentStep.load],
            type="primary",
        )
    with col2:
        st.button(
            "Create",
            on_click=set_form_step,
            args=["Jump", CurrentStep.editor],
            type="primary",
        )
