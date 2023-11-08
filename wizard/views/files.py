import pandas as pd
import streamlit as st

from core.data_types import convert_dtype
from core.files import file_from_upload
from core.files import file_from_url
from core.files import FILE_TYPES
from core.state import Field
from core.state import FileObject
from core.state import Metadata
from core.state import RecordSet
from utils import DF_HEIGHT
from utils import needed_field


def render_files():
    with st.form(key="manual_urls", clear_on_submit=True):
        url = None
        uploaded_file = None
        file_type_name = st.selectbox("Encoding format", options=FILE_TYPES.keys())
        st.divider()
        uploaded_file = st.file_uploader("Import from a local file")
        st.text("Or")
        url = st.text_input("Import from a URL")
        st.divider()
        submitted = st.form_submit_button("Add")
        if submitted:
            file_type = FILE_TYPES[file_type_name]
            # despite the api stating this, the default value for a text input is "" not None
            if url is not None and url != "":
                file = file_from_url(file_type, url)
            elif uploaded_file is not None:
                file = file_from_upload(file_type, uploaded_file)
            else:
                raise ValueError("should have either `url` or `uploaded_file`.")
            st.session_state[Metadata].add_distribution(file)
            # pandas has no idea how to display this (or how not to, to avoid errors, commenting out for now)
            # fields = [Field(name=k, data_type=convert_dtype(v)) for k,v in file.df.dtypes.items()],
            st.session_state[Metadata].add_record_set(
                RecordSet(
                    fields=[],
                    name=file.name + "_record_set",
                    description="",
                )
            )
    for key, file in enumerate(st.session_state[Metadata].distribution):
        with st.container():

            def delete_line():
                st.session_state[Metadata].remove_distribution(key)

            name = st.text_input(
                needed_field("Name"), value=file.name, key=f"{key}_name"
            )
            description = st.text_area(
                "Description",
                value=file.description,
                placeholder="Provide a clear description of the file.",
                key=f"{key}_description",
            )
            sha256 = st.text_input(
                needed_field("SHA256"),
                value=file.sha256,
                disabled=True,
                key=f"{key}_sha256",
            )
            encoding_format = st.text_input(
                needed_field("Encoding format"),
                value=file.encoding_format,
                disabled=True,
                key=f"{key}_encoding",
            )
            st.markdown("First rows of data:")
            st.dataframe(file.df, height=DF_HEIGHT)
            _, col = st.columns([5, 1])
            col.button("Remove", key=f"{key}_url", on_click=delete_line, type="primary")
            file = FileObject(
                name=name,
                description=description,
                content_url=file.content_url,
                encoding_format=encoding_format,
                sha256=sha256,
                df=file.df,
            )
            st.session_state[Metadata].update_distribution(key, file)
