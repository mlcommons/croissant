import os
from pathlib import Path
import tempfile

from core.state import CurrentStep
from core.state import Metadata
from core.state import set_form_step
import streamlit as st

import mlcroissant as mlc


def render_load():
    col1, col2 = st.columns([1,2], gap="small")
    with col1:
        file = st.file_uploader("Select a croissant file to load")
    if file is not None:
        try:
            file_cont = file.read()
            newfile_name = Path.home() / ".cache" / "croissant" / "loaded_croissant"
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