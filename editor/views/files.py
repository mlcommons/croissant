import enum

import streamlit as st

from components.tree import render_tree
from core.files import file_from_form
from core.files import file_from_upload
from core.files import file_from_url
from core.files import FILE_OBJECT
from core.files import FILE_SET
from core.files import FILE_TYPES
from core.files import RESOURCE_TYPES
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
_MANUAL_RESOURCE_TYPE_KEY = "create_manually_type"
_MANUAL_NAME_KEY = "manual_object_name"
_MANUAL_DESCRIPTION_KEY = "manual_object_description"
_MANUAL_SHA256_KEY = "manual_object_sha256"

Resource = FileObject | FileSet


class ResourceEvent(enum.Enum):
    """Event that triggers a resource change."""

    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    ENCODING_FORMAT = "ENCODING_FORMAT"
    SHA256 = "SHA256"
    CONTENT_SIZE = "CONTENT_SIZE"
    CONTENT_URL = "CONTENT_URL"


def handle_resource_change(event: ResourceEvent, resource: Resource, key: str):
    if event == ResourceEvent.NAME:
        resource.name = st.session_state[key]
    elif event == ResourceEvent.DESCRIPTION:
        resource.description = st.session_state[key]
    elif event == ResourceEvent.ENCODING_FORMAT:
        resource.license = st.session_state[key]
    elif event == ResourceEvent.SHA256:
        resource.citation = st.session_state[key]
    elif event == ResourceEvent.CONTENT_SIZE:
        resource.url = st.session_state[key]
    elif event == ResourceEvent.CONTENT_URL:
        resource.url = st.session_state[key]


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
            resource_type = st.selectbox(
                "Type", options=RESOURCE_TYPES, key=_MANUAL_RESOURCE_TYPE_KEY
            )
            st.text_input(
                needed_field("File name"),
                key=_MANUAL_NAME_KEY,
            )
            st.text_area(
                "File description",
                placeholder="Provide a clear description of the file.",
                key=_MANUAL_DESCRIPTION_KEY,
            )
            st.text_input(
                "SHA256",
                key=_MANUAL_SHA256_KEY,
            )
            st.text_input(
                "Parent",
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
            else:
                resource_type = st.session_state[_MANUAL_RESOURCE_TYPE_KEY]
                needs_sha256 = resource_type == FILE_OBJECT

                name = st.session_state[_MANUAL_NAME_KEY]
                description = st.session_state[_MANUAL_DESCRIPTION_KEY]
                sha256 = st.session_state[_MANUAL_SHA256_KEY] if needs_sha256 else None
                errorMessage = (
                    "Please import either a local file, provide a download URL or fill"
                    " in all required fields: name"
                )
                if needs_sha256:
                    errorMessage += " and SHA256"

                if not name or (needs_sha256 and not sha256):
                    # Some required fields are empty.
                    st.toast(
                        errorMessage,
                        icon="❌",
                    )
                    return
                file = file_from_form(
                    file_type, resource_type, name, description, sha256, names
                )

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

            if isinstance(file, FileObject):
                _render_file_object(key, file)
            else:
                _render_file_set(key, file)

            def delete_line():
                st.session_state[Metadata].remove_distribution(key)

            _, col = st.columns([5, 1])
            col.button("Remove", key=f"{key}_url", on_click=delete_line, type="primary")


def _render_file_object(prefix: int, file: FileObject):
    key = f"{prefix}_name"
    st.text_input(
        needed_field("Name"),
        value=file.name,
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.NAME, file, key),
    )
    key = f"{prefix}_description"
    st.text_area(
        "Description",
        value=file.description,
        placeholder="Provide a clear description of the file.",
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.DESCRIPTION, file, key),
    )
    key = f"{prefix}_sha256"
    st.text_input(
        needed_field("SHA256"),
        value=file.sha256,
        disabled=True,
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.SHA256, file, key),
    )
    key = f"{prefix}_encoding"
    st.text_input(
        needed_field("Encoding format"),
        value=file.encoding_format,
        disabled=True,
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.ENCODING_FORMAT, file, key),
    )
    st.markdown("First rows of data:")
    if file.df is not None:
        st.dataframe(file.df, height=DF_HEIGHT)
    else:
        st.text("No rendering possible.")


def _render_file_set(prefix: int, file: FileSet):
    key = f"{prefix}_name"
    st.text_input(
        needed_field("Name"),
        value=file.name,
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.NAME, file, key),
    )
    key = f"{prefix}_description"
    st.text_area(
        "Description",
        value=file.description,
        placeholder="Provide a clear description of the file.",
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.DESCRIPTION, file, key),
    )
    key = f"{prefix}_encoding"
    st.text_input(
        needed_field("Encoding format"),
        value=file.encoding_format,
        disabled=True,
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.ENCODING_FORMAT, file, key),
    )
