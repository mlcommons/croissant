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
    if timestamp and not force:
        project = CurrentProject.from_timestamp(timestamp)
        if (
            project
            and CurrentProject not in st.session_state
            and Metadata not in st.session_state
        ):
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

    # Uncomment those lines if you work locally in order to avoid clicks at each reload.
    # And comment all previous lines in `init_state`.
    # if mlc.Dataset not in st.session_state or force:
    #     st.session_state[mlc.Dataset] = mlc.Dataset("../datasets/titanic/metadata.json")
    # if Metadata not in st.session_state or force:
    #     st.session_state[Metadata] = Metadata.from_canonical(
    #         st.session_state[mlc.Dataset].metadata
    #     )
    # if CurrentProject not in st.session_state or force:
    #     st.session_state[CurrentProject] = CurrentProject.create_new()
