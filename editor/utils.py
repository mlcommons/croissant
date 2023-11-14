DF_HEIGHT = 150
import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
from core.state import SelectedResource
import mlcroissant as mlc

EDITOR_CACHE = mlc.constants.CROISSANT_CACHE / "editor"
LOADED_CROISSANT = EDITOR_CACHE / "loaded_croissant"


def needed_field(text: str) -> str:
    return f"{text}:red[*]"


def set_form_step(action, step=None):
    """Maintains the user's location within the editor."""
    if action == "Jump" and step is not None:
        st.session_state[CurrentStep] = step


def init_state():

    if Metadata not in st.session_state:
        st.session_state[Metadata] = Metadata()

    if mlc.Dataset not in st.session_state:
        st.session_state[mlc.Dataset] = None

    if CurrentStep not in st.session_state:
        st.session_state[CurrentStep] = CurrentStep.splash

    if SelectedResource not in st.session_state:
        st.session_state[SelectedResource] = None

    # Uncomment those lines if you work locally in order to avoid clicks at each reload.
    # And comment all previous lines in `init_state`.
    # if mlc.Dataset not in st.session_state:
    #     st.session_state[mlc.Dataset] = mlc.Dataset("../datasets/titanic/metadata.json")
    # if Metadata not in st.session_state:
    #     st.session_state[Metadata] = Metadata.from_canonical(
    #         st.session_state[mlc.Dataset].metadata
    #     )
    # if CurrentStep not in st.session_state:
    #     st.session_state[CurrentStep] = CurrentStep.editor
