import streamlit as st
import mlcroissant as mlc
import tempfile
from pathlib import Path
import os

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

        except mlc.ValidationError as e:
            st.warning(e)
            st.toast(body="Invalid Croissant File!", icon="🔥")