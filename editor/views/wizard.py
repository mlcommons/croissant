import json

import streamlit as st
import streamlit_nested_layout  # Do not remove this allows nesting columns.

from components.tabs import render_tabs
from core.constants import METADATA
from core.constants import OVERVIEW
from core.constants import RECORD_SETS
from core.constants import RESOURCES
from core.constants import TABS
from core.past_projects import save_current_project
from core.state import get_tab
from core.state import Metadata
from core.state import set_tab
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

    with col1:
        selected_tab = get_tab()
        selected_tab = render_tabs(tabs=TABS, selected_tab=selected_tab, key="tabs")
        if selected_tab == OVERVIEW or not selected_tab:
            render_overview()
        elif selected_tab == METADATA:
            render_metadata()
        elif selected_tab == RESOURCES:
            render_files()
        elif selected_tab == RECORD_SETS:
            render_record_sets()
        save_current_project()
        set_tab(selected_tab)
