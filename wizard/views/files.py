import pandas as pd
import streamlit as st

from components.tree import render_tree
from core.data_types import convert_dtype
from core.files import file_from_upload
from core.files import file_from_url
from core.files import FILE_TYPES
from core.state import Field
from core.state import FileObject
from core.state import FileSet
from core.state import Metadata
from core.state import RecordSet
from utils import DF_HEIGHT
from utils import needed_field

Resource = FileObject | FileSet


def render_files():
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        files = st.session_state[Metadata].distribution
        resource_name = _render_left_panel(files)
    with col2:
        if resource_name:
            _render_right_panel(resource_name)


def _render_left_panel(files: list[Resource]) -> Resource | None:
    """Renders the left panel: the list of all resources."""
    filename_to_file: dict[str, list[Resource]] = {}
    nodes = []
    for file in files:
        name = file.name
        filename_to_file[name] = file
        type = "FileObject" if isinstance(file, FileObject) else "FileSet"
        if file.contained_in:
            parent = file.contained_in
        else:
            parent = None
        nodes.append({"name": name, "type": type, "parent": parent})
    _render_upload_form()
    name = render_tree(nodes)
    if not name:
        return None
    file = filename_to_file[name]
    return file


def _render_upload_form():
    """Renders the form to upload from local or upload from URL."""
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


def _render_right_panel(selected_file: Resource):
    """Renders the left panel: the detail of the selected resource."""
    for key, file in enumerate(st.session_state[Metadata].distribution):
        if file == selected_file:

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
