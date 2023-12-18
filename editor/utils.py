import streamlit as st

from core.past_projects import open_project
from core.query_params import get_project_timestamp
from core.state import CurrentProject
from core.state import Metadata
from core.state import OpenTab
from core.state import SelectedRecordSet
from core.state import SelectedResource
import mlcroissant as mlc


def needed_field(text: str) -> str:
    return f"{text}:red[*]"


def init_state(force=False):
    """Initializes the session state. `force=True` to force re-initializing it."""

    timestamp = get_project_timestamp()
    if CurrentProject not in st.session_state or force:
        if timestamp:
            project = CurrentProject.from_timestamp(timestamp)
            if project:
                st.session_state[CurrentProject] = project
                st.session_state[Metadata] = open_project(project.path)
        else:
            st.session_state[CurrentProject] = None

    if Metadata not in st.session_state or force:
        st.session_state[Metadata] = Metadata()

    if mlc.Dataset not in st.session_state or force:
        st.session_state[mlc.Dataset] = None

    if SelectedResource not in st.session_state or force:
        st.session_state[SelectedResource] = None

    if SelectedResource not in st.session_state or force:
        st.session_state[SelectedRecordSet] = None

    if OpenTab not in st.session_state or force:
        st.session_state[OpenTab] = None
