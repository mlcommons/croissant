from state import init_state
from views.jsonld import render_jsonld
from views.side_buttons import render_side_buttons
from views.wizard import render_wizard
from views.load import render_load
import streamlit as st

init_state()

st.set_page_config(page_title="Croissant Wizard", layout="wide")
st.header("Croissant Wizard")

render_side_buttons()

col1, col2 = st.columns([3, 3], gap="medium")
with col1:
    render_wizard()
with col2:
    render_load()


