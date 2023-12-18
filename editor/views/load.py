import os

from etils import epath
import streamlit as st

from core.constants import EDITOR_CACHE
from core.past_projects import save_current_project
from core.state import Metadata
import mlcroissant as mlc

_JSON_LD_INFO = """You can download JSON-LD Croissant files from major dataset
providers:

- [Kaggle](https://www.kaggle.com/datasets) embeds Croissant JSON-LD directly in their
HTML.
- [OpenML](https://www.openml.org/search?type=data) offers a 🥐 button on all of their
datasets.
- [Hugging Face](https://huggingface.co/) offers an
[API endpoint](https://datasets-server.huggingface.co/croissant?dataset=${dataset_id) to
build a Croissant JSON-LD."""


def _on_file_upload(key):
    """Triggers when a new file gets uploaded to load the Croissant metadata."""
    file = st.session_state[key]
    file_cont = file.read()
    # TODO(marcenacp): The Python library should support loading from an open file/dict.
    newfile_name = EDITOR_CACHE / "loaded_croissant"
    os.makedirs(os.path.dirname(newfile_name), exist_ok=True)
    with open(newfile_name, mode="wb+") as outfile:
        outfile.write(file_cont)
    try:
        dataset = mlc.Dataset(newfile_name)
        st.session_state[Metadata] = Metadata.from_canonical(dataset.metadata)
        save_current_project()
    except mlc.ValidationError as e:
        st.warning(e)
        st.toast(body="Invalid Croissant File!", icon="🔥")


def render_load():
    key = "json-ld-file-upload"
    st.info(_JSON_LD_INFO)
    st.file_uploader(
        "Drop a JSON-LD", type="json", key=key, on_change=_on_file_upload, args=(key,)
    )
