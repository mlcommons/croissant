import logging
import pickle

from etils import epath
import streamlit as st

from core.constants import PAST_PROJECTS_PATH
from core.query_params import set_project
from core.state import CurrentProject
from core.state import FileObject
from core.state import get_user
from core.state import Metadata


def load_past_projects_paths() -> list[epath.Path]:
    user = get_user()
    past_projects_path = PAST_PROJECTS_PATH(user)
    past_projects_path.mkdir(parents=True, exist_ok=True)
    return sorted(list(past_projects_path.iterdir()), reverse=True)


def _pickle_file(path: epath.Path) -> epath.Path:
    return path / ".metadata.pkl"


def save_current_project():
    metadata: Metadata = st.session_state[Metadata]
    project = st.session_state.get(CurrentProject)
    if not project:
        project = CurrentProject.create_new()
        st.session_state[CurrentProject] = project
    project.path.mkdir(parents=True, exist_ok=True)
    set_project(project)
    # FileObjects should have a folder.
    for resource in metadata.distribution:
        if isinstance(resource, FileObject):
            resource.folder = project.path
    try:
        pickled = pickle.dumps(metadata)
        _pickle_file(project.path).write_bytes(pickled)
    except pickle.PicklingError as e:
        logging.error("Could not pickle metadata.", exc_info=True)


def open_project(path: epath.Path) -> Metadata:
    with _pickle_file(path).open("rb") as file:
        return pickle.load(file)
