from core.state import CurrentStep
from core.state import init_state
import streamlit as st
from views.jsonld import render_jsonld
from views.load import render_load
from views.side_buttons import render_side_buttons
from views.splash import render_splash
from views.wizard import render_wizard


def init_state():

    if Metadata not in st.session_state:
        st.session_state[Metadata] = Metadata()

    if mlc.Dataset not in st.session_state:
        st.session_state[mlc.Dataset] = None

    if CurrentStep not in st.session_state:
        st.session_state[CurrentStep] = "start"

def set_form_step(action, step=None):
    """Maintains the user's location within the wizard."""
    if action == "Jump" and step is not None:
        st.session_state[CurrentStep] = step

init_state()

st.set_page_config(page_title="Croissant Wizard", layout="wide")
st.header("Croissant Wizard")



if st.session_state[CurrentStep] == CurrentStep.start:
    render_splash()
elif st.session_state[CurrentStep] == CurrentStep.load:
    render_load()
elif st.session_state[CurrentStep] == CurrentStep.editor:
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        render_wizard()
else:
    st.warning("invalid unhandled app state")

