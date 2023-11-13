import json

from core.state import Metadata
import streamlit as st
from views.files import render_files
from views.metadata import render_metadata
from views.record_sets import render_record_sets

import mlcroissant as mlc


def render_download_button():
    try:
        st.download_button(
            "Save",
            file_name="croissant.json",
            type="primary",
            data=json.dumps(st.session_state[Metadata].to_canonical().to_json()),
        )
    except mlc.ValidationError as exception:
        st.download_button("Save", disabled=True, data="")


def render_wizard():
    with st.expander("Metadata", expanded=True):
        render_metadata()
    with st.expander("Files"):
        render_files()
    with st.expander("Record Sets"):
        render_record_sets()
    render_download_button()
