import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
import mlcroissant as mlc
from utils import init_state
from views.jsonld import render_jsonld
from views.load import render_load
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
else:
    st.warning("invalid unhandled app state")
