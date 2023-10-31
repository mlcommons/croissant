from state import init_state
from state import CurrentStep
from views.jsonld import render_jsonld
from views.side_buttons import render_side_buttons
from views.wizard import render_wizard
from views.load import render_load
from views.splash import render_splash
import streamlit as st

init_state()

st.set_page_config(page_title="Croissant Wizard", layout="wide")
st.header("Croissant Wizard")



if st.session_state[CurrentStep] == "start":
    render_splash()
    st.stop()
if st.session_state[CurrentStep] == "load":
    render_load()
    st.stop()
if st.session_state[CurrentStep] != "editor":
    raise Exception("invalid unhandled app state")

render_side_buttons()


col1, col2 = st.columns([1, 1], gap="medium")
with col1:
    render_wizard()
with col2:
    pass
    #render_errors()
