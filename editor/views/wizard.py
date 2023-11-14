import json

import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
import mlcroissant as mlc
from views.files import render_files
from views.metadata import render_metadata
from views.overview import render_overview
from views.record_sets import render_record_sets


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


OVERVIEW = "Overview"
METADATA = "Metadata"
RESOURCES = "Resources"
RECORD_SETS = "RecordSets"


def render_editor():
    tab1, tab2, tab3, tab4 = st.tabs([OVERVIEW, METADATA, RESOURCES, RECORD_SETS])

    with tab1:
        render_overview()
    with tab2:
        render_metadata()
    with tab3:
        render_files()
    with tab4:
        render_record_sets()
    render_download_button()
