import json

import streamlit as st
import streamlit_nested_layout  # Do not remove this allows nesting columns.

from core.constants import TABS
from core.past_projects import save_current_project
from core.query_params import go_to_tab
from core.state import Metadata
import mlcroissant as mlc
from views.files import render_files
from views.metadata import render_metadata
from views.overview import render_overview
from views.record_sets import render_record_sets


def render_export_button(col):
    metadata: Metadata = st.session_state[Metadata]
    try:
        col.download_button(
            "Export",
            file_name=f"croissant-{metadata.name.lower()}.json",
            type="primary",
            data=json.dumps(metadata.to_canonical().to_json()),
            help="Export the Croissant JSON-LD",
        )
    except mlc.ValidationError as exception:
        col.download_button("Export", disabled=True, data="", help=str(exception))


def render_editor():
    col1, col2 = st.columns([10, 1])
    render_export_button(col2)
    tab1, tab2, tab3, tab4 = col1.tabs(TABS)

    with tab1:
        render_overview()
    with tab2:
        render_metadata()
    with tab3:
        render_files()
    with tab4:
        render_record_sets()
    save_current_project()
