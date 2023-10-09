from state import CurrentStep
from state import File
from state import Files
from state import Metadata
from state import RecordSets
import streamlit as st
from views.st_croissant_file import render_croissant_file
from views.st_side_buttons import render_side_buttons
from views.st_wizard import render_wizard

if CurrentStep not in st.session_state:
    st.session_state[CurrentStep] = 1

if Files not in st.session_state:
    st.session_state[Files] = []

if Metadata not in st.session_state:
    st.session_state[Metadata] = Metadata()

if RecordSets not in st.session_state:
    st.session_state[RecordSets] = []

st.set_page_config(page_title="Croissant Wizard", layout="wide")
st.header("Croissant Wizard")
col1, col2, col3 = st.columns([1, 3, 3], gap="medium")
with col1:
    render_side_buttons()
with col2:
    render_wizard()
with col3:
    render_croissant_file()
