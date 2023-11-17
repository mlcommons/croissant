import pandas as pd
import streamlit as st

from components.tree import render_tree
from core.files import file_from_upload
from core.files import file_from_url
from core.files import FILE_TYPES
from core.record_sets import infer_record_sets
from core.state import FileObject
from core.state import FileSet
from core.state import Metadata
from core.state import SelectedResource
from utils import DF_HEIGHT
from utils import needed_field

Resource = FileObject | FileSet

_DISTANT_URL_KEY = "import_from_url"
_LOCAL_FILE_KEY = "import_from_local_file"


def render_files():
    col1, col2, col3 = st.columns([1, 1, 1], gap="small")
    with col1:
        st.subheader("Upload more resources")
        _render_upload_panel()
    with col2:
        st.subheader("Uploaded resources")
        files = st.session_state[Metadata].distribution
        resource = _render_resources_panel(files)
        st.session_state[SelectedResource] = resource
    with col3:
        _render_right_panel()


def _render_resources_panel(files: list[Resource]) -> Resource | None:
    """Renders the left panel: the list of all resources."""
    filename_to_file: dict[str, list[Resource]] = {}
    nodes = []
    for file in files:
        name = file.name
        filename_to_file[name] = file
        type = "FileObject" if isinstance(file, FileObject) else "FileSet"
        if file.contained_in:
            if isinstance(file.contained_in, list):
                parents = file.contained_in
            else:
                parents = [file.contained_in]
        else:
            parents = []
        nodes.append({"name": name, "type": type, "parents": parents})

    name = None
    if nodes:
        name = render_tree(nodes, key="-".join([node["name"] for node in nodes]))
    else:
        st.write("No resource yet.")

    if not name:
        return None
    file = filename_to_file[name]
    return file


def _render_upload_panel():
    """Renders the form to upload from local or upload from URL."""
    with st.form(key="upload_form", clear_on_submit=True):
        file_type_name = st.selectbox("Encoding format", options=FILE_TYPES.keys())
        tab1, tab2, tab3 = st.tabs([
            "Import from a local file", "Import from a URL", "Add manually"
        ])

        with tab1:
            st.file_uploader("Select a file", key=_LOCAL_FILE_KEY)

        with tab2:
            st.text_input("URL:", key=_DISTANT_URL_KEY)

        with tab3:
            resource_type = st.selectbox("Type", options=["FileObject", "FileSet"])

            file = FileObject() if resource_type == "FileObject" else FileSet()

            name = st.text_input(
                needed_field("File name"), value=file.name, key="manual_name"
            )
            description = st.text_area(
                "File description",
                value=file.description,
                placeholder="Provide a clear description of the file.",
                key="manual_description",
            )
            sha256 = st.text_input(
                needed_field("SHA256"),
                value=file.sha256,
                disabled=True,
                key="manual_sha256",
            )
            parent = st.text_input(
                needed_field("Parent"),
                value=file.encoding_format,
                key="manual_parent",
            )

        def handle_on_click():
            url = st.session_state[_DISTANT_URL_KEY]
            uploaded_file = st.session_state[_LOCAL_FILE_KEY]
            file_type = FILE_TYPES[file_type_name]
            nodes = (
                st.session_state[Metadata].distribution
                + st.session_state[Metadata].record_sets
            )
            names = set([node.name for node in nodes])
            if url:
                file = file_from_url(file_type, url, names)
            elif uploaded_file:
                file = file_from_upload(file_type, uploaded_file, names)
            # todo: handle manually created resource.
            else:
                st.toast("Please, import either a local file or a URL.", icon="❌")
                return
            st.session_state[Metadata].add_distribution(file)
            record_sets = infer_record_sets(file, names)
            for record_set in record_sets:
                st.session_state[Metadata].add_record_set(record_set)
            st.session_state[SelectedResource] = file.name

        st.form_submit_button("Upload", on_click=handle_on_click)


def _render_right_panel():
    """Renders the right panel: either a form to create a resource or details
    of the selected resource."""
    if st.session_state.get(SelectedResource):
        _render_resource_details(st.session_state[SelectedResource])


def _render_resource_details(selected_file: Resource):
    """Renders the details of the selected resource."""
    file: FileObject | FileSet
    for key, file in enumerate(st.session_state[Metadata].distribution):
        if file.name == selected_file.name:

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
            if file.df is not None:
                st.dataframe(file.df, height=DF_HEIGHT)
            else:
                st.text("No rendering possible.")
            _, col = st.columns([5, 1])
            col.button("Remove", key=f"{key}_url", on_click=delete_line, type="primary")
            file = FileObject(
                name=name,
                description=description,
                content_url=file.content_url,
                content_size=file.content_size,
                encoding_format=encoding_format,
                sha256=sha256,
                df=file.df,
            )
            st.session_state[Metadata].update_distribution(key, file)
