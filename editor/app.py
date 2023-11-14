import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
import mlcroissant as mlc
from utils import init_state
from views.splash import render_splash
from views.wizard import render_editor

init_state()

st.set_page_config(page_title="Croissant Editor", layout="wide")
st.header("Croissant Editor")


if st.session_state[CurrentStep] == CurrentStep.splash:
    render_splash()
elif st.session_state[CurrentStep] == CurrentStep.editor:
    render_editor()
else:
    st.warning("invalid unhandled app state")
