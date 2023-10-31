import streamlit as st
from views.side_buttons import set_form_step

def render_splash():
    st.text("Welcome to the Croissant Wizard, would you like to load an existing croissant file, or create a new one?")
    col1, col2, col3 = st.columns([1,1,8], gap="small")
    with col1:
        st.button(
            "Load",
            on_click=set_form_step,
            args=["Jump", "load"],
            type="primary",
        )
    with col2:
        st.button(
            "Create",
            on_click=set_form_step,
            args=["Jump", "editor"],
            type="primary",
        )