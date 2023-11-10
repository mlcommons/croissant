import os
import tempfile

from etils import epath
import streamlit as st

from core.state import CurrentStep
from core.state import Metadata
import mlcroissant as mlc
from utils import LOADED_CROISSANT
from utils import set_form_step


def render_load():
    col1, col2 = st.columns([1, 2], gap="small")
    with col1:
        file = st.file_uploader("Select a croissant file to load")
    if file is not None:
        try:
            file_cont = file.read()
            newfile_name = (
                epath.Path("~").expanduser()
                / ".cache"
                / "croissant"
                / "loaded_croissant"
            )
            os.makedirs(os.path.dirname(newfile_name), exist_ok=True)
            with open(newfile_name, mode="wb+") as outfile:
                outfile.write(file_cont)
            dataset = mlc.Dataset(newfile_name)
            st.session_state[Metadata] = Metadata.from_canonical(dataset)
            set_form_step("Jump", CurrentStep.editor)
            st.rerun()
        except mlc.ValidationError as e:
            st.warning(e)
            st.toast(body="Invalid Croissant File!", icon="🔥")
