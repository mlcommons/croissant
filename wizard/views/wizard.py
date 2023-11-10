import streamlit as st

from core.state import CurrentStep
from views.files import render_files
from views.metadata import render_metadata
from views.overview import render_overview
from views.record_sets import render_record_sets

OVERVIEW = "Overview"
METADATA = "Metadata"
RESOURCES = "Resources"
RECORD_SETS = "Record sets"


def render_wizard():
    tab1, tab2, tab3, tab4 = st.tabs([OVERVIEW, METADATA, RESOURCES, RECORD_SETS])

    with tab1:
        render_overview()
    with tab2:
        render_metadata()
    with tab3:
        render_files()
    with tab4:
        render_record_sets()
