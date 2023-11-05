from state import CurrentStep
from state import init_state
import streamlit as st
from views.jsonld import render_jsonld
from views.load import render_load
from views.side_buttons import render_side_buttons
from views.splash import render_splash
from views.wizard import render_wizard

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
elif st.session_state[CurrentStep] == CurrentStep.overview:
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        render_overview()
    with col2:
        render_errors()
else:
    st.warning("invalid unhandled app state")
