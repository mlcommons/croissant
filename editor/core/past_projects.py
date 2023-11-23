import logging
import pickle

from etils import epath
import streamlit as st

from core.constants import PAST_PROJECTS_PATH
from core.state import CurrentProject
from core.state import Metadata


def load_past_projects_paths() -> list[epath.Path]:
    PAST_PROJECTS_PATH.mkdir(parents=True, exist_ok=True)
    return sorted(list(PAST_PROJECTS_PATH.iterdir()), reverse=True)


def _pickle_file(path: epath.Path) -> epath.Path:
    return path / ".metadata.pkl"


def save_current_project():
    metadata = st.session_state[Metadata]
    project = st.session_state[CurrentProject]
    project.path.mkdir(parents=True, exist_ok=True)
    with _pickle_file(project.path).open("wb") as file:
        try:
            pickle.dump(metadata, file)
        except pickle.PicklingError:
            logging.error("Could not pickle metadata.")


def open_project(path: epath.Path) -> Metadata:
    with _pickle_file(path).open("rb") as file:
        return pickle.load(file)
