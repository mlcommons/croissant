import os
import tempfile

import streamlit as st
from utils import LOADED_CROISSANT

import mlcroissant as mlc


def render_load():
    col1, col2 = st.columns([1,2], gap="small")
    with col1:
        file = st.file_uploader("Select a croissant file to load")
    if file is not None:
        try:
            content = file.read()
            new_file_name = LOADED_CROISSANT / "current_loaded_croissant.json"
            os.makedirs(os.path.dirname(LOADED_CROISSANT), exist_ok=True)
            with open(new_file_name, mode="wb+") as outfile:
                outfile.write(content)
            dataset = mlc.Dataset(new_file_name)
            

        except mlc.ValidationError as e:
            st.warning(e)
            st.toast(body="Invalid Croissant File!", icon="🔥")