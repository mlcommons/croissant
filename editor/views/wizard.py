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


def _export_json() -> str | None:
    metadata: Metadata = st.session_state[Metadata]
    try:
        name = metadata.name or "metadata"
        return {
            "name": f"croissant-{name.lower()}.json",
            "content": json.dumps(metadata.to_canonical().to_json()),
        }
    except mlc.ValidationError as exception:
        return None


def render_editor():
    export_json = _export_json()

    # Warning: the custom component cannot be nested in a st.columns or it is forced to
    # re-render even if a `key` is set.
    selected_tab = get_tab()
    tab = render_tabs(
        tabs=TABS, selected_tab=selected_tab, json=export_json, key="tabs"
    )
    if tab == OVERVIEW:
        render_overview()
    elif tab == METADATA:
        render_metadata()
    elif tab == RESOURCES:
        render_files()
    elif tab == RECORD_SETS:
        render_record_sets()
    save_current_project()
    set_tab(tab)
