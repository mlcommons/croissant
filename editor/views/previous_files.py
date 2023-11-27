import datetime

from etils import epath
import streamlit as st

from core.constants import PROJECT_FOLDER_PATTERN
from core.past_projects import load_past_projects_paths
from core.past_projects import open_project
from core.query_params import set_project
from core.state import CurrentProject
from core.state import Metadata


def _load_croissant(metadata: Metadata, path: epath.Path) -> None:
    st.session_state[Metadata] = metadata
    project = CurrentProject(path)
    st.session_state[CurrentProject] = project
    set_project(project)


def _remove_croissant(path: epath.Path) -> None:
    path.rmtree(missing_ok=True)


def render_previous_files():
    paths = load_past_projects_paths()
    if not paths:
        st.write("No past project to load. Create one on the left!")
    else:
        for index, path in enumerate(paths):
            try:
                metadata = open_project(path)
                timestamp = datetime.datetime.strptime(
                    path.name, PROJECT_FOLDER_PATTERN
                ).strftime("%Y/%m/%d %H:%M")
                label = f"{metadata.name or 'Unnamed dataset'} - {timestamp}"
                col1, col2 = st.columns([10, 1])
                col1.button(
                    label,
                    key=f"splash-{index}-load",
                    on_click=_load_croissant,
                    args=(metadata, path),
                )
                col2.button(
                    "✖️",
                    help="Warning: this will delete the project.",
                    key=f"splash-{index}-remove",
                    on_click=_remove_croissant,
                    args=(path,),
                )
            except:
                pass
