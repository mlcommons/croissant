import logging

import requests
import streamlit as st

from core.constants import OAUTH_CLIENT_ID
from core.past_projects import save_current_project
from core.query_params import set_project
from core.state import CurrentProject
from core.state import Metadata
import mlcroissant as mlc
from views.load import render_load
from views.previous_files import render_previous_files


def render_splash():
    if OAUTH_CLIENT_ID:
        st.info(
            "**Disclaimer**: Do not put sensitive information or datasets here. The"
            " storage on Hugging Face Spaces is ephemeral. If you want to host your own"
            " version locally, build the app from [the GitHub"
            " repository](https://github.com/mlcommons/croissant/tree/main/editor)."
        )
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        with st.expander("**Load an existing Croissant JSON-LD file**", expanded=True):
            render_load()
        with st.expander("**Create from scratch**", expanded=True):

            def create_new_croissant():
                st.session_state[Metadata] = Metadata()
                save_current_project()

            st.button(
                "Create",
                on_click=create_new_croissant,
                type="primary",
            )
        with st.expander("**Try out an example!**", expanded=True):

            def create_example(dataset: str):
                url = f"https://raw.githubusercontent.com/mlcommons/croissant/main/datasets/{dataset.lower()}/metadata.json"
                try:
                    json = requests.get(url).json()
                    metadata = mlc.Metadata.from_json(mlc.Issues(), json, None)
                    st.session_state[Metadata] = Metadata.from_canonical(metadata)
                    save_current_project()
                except Exception as exception:
                    logging.error(exception)
                    st.error(
                        "Sorry, it seems that the example is broken... Can you please"
                        " [open an issue on"
                        " GitHub](https://github.com/mlcommons/croissant/issues/new)?"
                    )

            dataset = st.selectbox(
                label="Dataset",
                options=[
                    "Titanic",
                    "FLORES-200",
                    "GPT-3",
                    "COCO2014",
                    "PASS",
                    "MovieLens",
                    "Bigcode-The-Stack",
                ],
            )
            st.button(
                f"{dataset} dataset",
                on_click=create_example,
                type="primary",
                args=(dataset,),
            )
    with col2:
        with st.expander("**Past projects**", expanded=True):
            render_previous_files()
