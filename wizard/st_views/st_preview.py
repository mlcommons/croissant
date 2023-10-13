from st_state import Metadata
from st_state import Files
from st_state import RecordSets
from st_views.st_jsonld import render_jsonld
import streamlit as st

def preview_metadata_():
    if st.session_state[Metadata]:
        # todo
        st.write('Metadata has been created')

def preview_files_():
    if st.session_state[Files]:
        # todo
        st.write('Files has been created')

def preview_record_sets_():
    if st.session_state[RecordSets]:
        # todo
        st.write('RecordSets has been created')

def render_preview():
    show_json = st.toggle("Show JSON")

    if (show_json):
        # Show the config
        render_jsonld()
    else:
        preview_metadata_()
        preview_files_()
        preview_record_sets_()
