import logging
import pickle

from etils import epath
import streamlit as st

from core.constants import PAST_PROJECTS_PATH
from core.state import CurrentProject
from core.state import Metadata
from core.state import User


def load_past_projects_paths() -> list[epath.Path]:
    user = st.session_state.get(User)
    past_projects_path = PAST_PROJECTS_PATH(user)
    past_projects_path.mkdir(parents=True, exist_ok=True)
    return sorted(list(past_projects_path.iterdir()), reverse=True)


def _pickle_file(path: epath.Path) -> epath.Path:
    return path / ".metadata.pkl"


def save_current_project():
    metadata = st.session_state[Metadata]
    project = st.session_state.get(CurrentProject)
    if not project:
        project = CurrentProject.create_new()
        st.session_state[CurrentProject] = project
    project.path.mkdir(parents=True, exist_ok=True)
    with _pickle_file(project.path).open("wb") as file:
        try:
            pickle.dump(metadata, file)
        except pickle.PicklingError:
            logging.error("Could not pickle metadata.")


def open_project(path: epath.Path) -> Metadata:
    with _pickle_file(path).open("rb") as file:
        return pickle.load(file)
