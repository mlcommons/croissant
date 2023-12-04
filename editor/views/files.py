from etils import epath
import streamlit as st

from components.tree import render_tree
from core.constants import DF_HEIGHT
from core.constants import OAUTH_CLIENT_ID
from core.files import code_to_index
from core.files import file_from_form
from core.files import file_from_upload
from core.files import file_from_url
from core.files import FILE_OBJECT
from core.files import FILE_SET
from core.files import FILE_TYPES
from core.files import is_url
from core.files import RESOURCE_TYPES
from core.files import trigger_download
from core.path import get_resource_path
from core.record_sets import infer_record_sets
from core.state import CurrentProject
from core.state import FileObject
from core.state import FileSet
from core.state import Metadata
from core.state import SelectedResource
from events.resources import handle_resource_change
from events.resources import ResourceEvent
from utils import needed_field

Resource = FileObject | FileSet

_DISTANT_URL_KEY = "import_from_url"
_LOCAL_FILE_KEY = "import_from_local_file"
_MANUAL_RESOURCE_TYPE_KEY = "create_manually_type"

_INFO = """Resources can be `FileObjects` (single files) or `FileSets` (sets of files 
with the same MIME type). On this page, you can upload `FileObjects`, point to external
resources on the web or manually create new resources."""


def render_files():
    """Renders the views of the files: warnings and panels to display information."""
    _render_warnings()
    col1, col2, col3 = st.columns([1, 1, 1], gap="small")
    with col1:
        st.markdown("##### Upload more resources")
        _render_upload_panel()
    with col2:
        st.markdown("##### Uploaded resources")
        files = st.session_state[Metadata].distribution
        resource = _render_resources_panel(files)
        st.session_state[SelectedResource] = resource
    with col3:
        _render_right_panel()


def _render_warnings():
    """Renders warnings concerning local files."""
    metadata: Metadata = st.session_state[Metadata]
    warning = ""
    for resource in metadata.distribution:
        if not isinstance(resource, FileObject):
            continue
        content_url = resource.content_url
        if content_url and not content_url.startswith("http"):
            path = get_resource_path(content_url)
            if not path.exists():
                if OAUTH_CLIENT_ID:
                    warning += (
                        f'⚠️ Resource "{resource.name}" points to a local file that'
                        " doesn't exist on the disk. Fix this by changing the content"
                        " URL.\n\n"
                    )
                else:
                    warning += (
                        f'⚠️ Resource "{resource.name}" points to a local file that'
                        " doesn't exist on the disk. Fix this by either downloading"
                        f" it to {path} or changing the content URL.\n\n"
                    )
    if warning:
        st.warning(warning.strip())


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
        tab1, tab2, tab3 = st.tabs([
            "Import from a local file", "Import from a URL", "Add manually"
        ])

        with tab1:
            st.file_uploader("Select a file", key=_LOCAL_FILE_KEY)

        with tab2:
            st.text_input("URL:", key=_DISTANT_URL_KEY)

        with tab3:
            st.selectbox("Type", options=RESOURCE_TYPES, key=_MANUAL_RESOURCE_TYPE_KEY)

        def handle_on_click():
            url = st.session_state[_DISTANT_URL_KEY]
            uploaded_file = st.session_state[_LOCAL_FILE_KEY]
            metadata: Metadata = st.session_state[Metadata]
            names = metadata.names()
            project: CurrentProject = st.session_state[CurrentProject]
            folder = project.path
            if url:
                file = file_from_url(url, names, folder)
            elif uploaded_file:
                file = file_from_upload(uploaded_file, names, folder)
            else:
                resource_type = st.session_state[_MANUAL_RESOURCE_TYPE_KEY]
                file = file_from_form(resource_type, names, folder)

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
    else:
        st.info(_INFO, icon="💡")


def _render_resource_details(selected_file: Resource):
    """Renders the details of the selected resource."""
    file: FileObject | FileSet
    for i, file in enumerate(st.session_state[Metadata].distribution):
        if file.name == selected_file.name:
            is_file_object = isinstance(file, FileObject)
            index = (
                RESOURCE_TYPES.index(FILE_OBJECT)
                if is_file_object
                else RESOURCE_TYPES.index(FILE_SET)
            )
            key = f"{i}-file-name"
            st.selectbox(
                "Type",
                index=index,
                options=RESOURCE_TYPES,
                key=key,
                on_change=handle_resource_change,
                args=(ResourceEvent.TYPE, file, key),
            )

            _render_resource(i, file, is_file_object)

            def delete_line():
                st.session_state[Metadata].remove_distribution(i)

            def close():
                st.session_state[SelectedResource] = None

            col1, col2 = st.columns([1, 1])
            col1.button("Close", key=f"{i}_close", on_click=close, type="primary")
            col2.button(
                "⚠️ Remove", key=f"{i}_remove", on_click=delete_line, type="secondary"
            )


def _render_resource(prefix: int, file: Resource, is_file_object: bool):
    parent_options = [f.name for f in st.session_state[Metadata].distribution]
    key = f"{prefix}_parents"
    st.multiselect(
        "Parents",
        default=file.contained_in,
        options=parent_options,
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.CONTAINED_IN, file, key),
    )
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
    if is_file_object:
        key = f"{prefix}_content_url"
        st.text_input(
            needed_field("Content URL"),
            value=file.content_url,
            key=key,
            on_change=handle_resource_change,
            args=(ResourceEvent.CONTENT_URL, file, key),
        )
        key = f"{prefix}_sha256"
        st.text_input(
            needed_field("SHA256"),
            value=file.sha256,
            key=key,
            on_change=handle_resource_change,
            args=(ResourceEvent.SHA256, file, key),
        )
        key = f"{prefix}_content_size"
        st.text_input(
            "Content size",
            value=file.content_size,
            key=key,
            on_change=handle_resource_change,
            args=(ResourceEvent.CONTENT_SIZE, file, key),
        )
    else:
        key = f"{prefix}_includes"
        st.text_input(
            needed_field("Glob pattern of files to include"),
            value=file.includes,
            key=key,
            on_change=handle_resource_change,
            args=(ResourceEvent.INCLUDES, file, key),
        )
    key = f"{prefix}_encoding"
    st.selectbox(
        needed_field("Encoding format"),
        index=code_to_index(file.encoding_format),
        options=FILE_TYPES.keys(),
        key=key,
        on_change=handle_resource_change,
        args=(ResourceEvent.ENCODING_FORMAT, file, key),
    )
    if is_file_object:
        st.markdown("First rows of data:")
        if file.df is not None:
            st.dataframe(file.df, height=DF_HEIGHT)
        else:
            st.button(
                "Trigger download",
                disabled=bool(file.content_url),
                on_click=trigger_download,
                args=(file,),
            )
