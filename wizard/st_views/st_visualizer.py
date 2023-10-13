from st_state import Metadata
from st_state import Files
from st_state import RecordSets
from st_views.st_jsonld import render_jsonld
import pandas as pd
import streamlit as st

def preview_metadata_():
    if st.session_state[Metadata]:
        md = st.session_state[Metadata]
        df = pd.DataFrame(
            [[md.name], [md.url], [md.license], [md.description], [md.citation]], 
            columns=(["Dataset metadata"]),
            index=(["Name", "URL", "Licence", "Description", "Citation"]))
        st.table(df)


def preview_files_():
    if st.session_state[Files]:
        # todo
        return

def preview_record_sets_():
    if st.session_state[RecordSets]:
        # todo
        return

def render_preview():
    show_json = st.toggle("Show the full Croissant config")

    if (show_json):
        # Show the config
        render_jsonld()
    else:
        preview_metadata_()
        preview_files_()
        preview_record_sets_()
