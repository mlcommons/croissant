import datetime

import streamlit as st

from core.past_projects import load_past_projects
from core.past_projects import loaded_project
from core.state import CurrentStep
from core.state import Metadata
from utils import set_form_step


def render_previous_files():
    past_projects = load_past_projects()
    if not past_projects:
        st.text("No past Projects to load!")
    else:

        def load_croissant(index: int, metadata: Metadata) -> None:
            st.session_state[Metadata] = metadata
            set_form_step("Jump", CurrentStep.editor)
            loaded_project(index)

        for index, project in enumerate(past_projects):
            st.button(
                f"{project[0].name} - "
                f"{datetime.datetime.fromtimestamp(project[1]).strftime('%Y-%m-%d %H:%M:%S')}",
                key=project[0].name + "_" + str(index),
                on_click=load_croissant,
                args=[index, project[0]],
            )
