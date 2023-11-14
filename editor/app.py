import streamlit as st

from core.state import CurrentStep
from utils import init_state
from views.splash import render_splash
from views.wizard import render_editor

init_state()


def _back_to_menu():
    """Sends the user back to the menu."""
    st.session_state[CurrentStep] = CurrentStep.splash


st.set_page_config(page_title="Croissant Editor", page_icon="🥐", layout="wide")
col1, col2 = st.columns([10, 1])
col1.header("Croissant Editor")
if st.session_state[CurrentStep] != CurrentStep.splash:
    col2.button("Menu", on_click=_back_to_menu)


if st.session_state[CurrentStep] == CurrentStep.splash:
    render_splash()
elif st.session_state[CurrentStep] == CurrentStep.editor:
    render_editor()
else:
    st.warning("invalid unhandled app state")
