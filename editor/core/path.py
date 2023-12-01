from etils import epath
import streamlit as st

from core.state import CurrentProject


def get_resource_path(content_url: str) -> epath.Path:
    """Gets the path on disk of the resource with `content_url`."""
    project: CurrentProject = st.session_state[CurrentProject]
    path = project.path / content_url
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    return path
