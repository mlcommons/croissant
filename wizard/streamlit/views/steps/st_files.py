from core.data_types import convert_dtype
from core.files import check_file
import pandas as pd
from state import File
from state import Files
from state import RecordSets
import streamlit as st
from views.st_utils import DF_HEIGHT
from views.st_utils import needed_field

FILE_TYPES = ["text/csv"]


def render_files():
    with st.form(key="manual_urls", clear_on_submit=True):
        file_type = st.selectbox("Encoding format", options=FILE_TYPES)
        url = st.text_input("Import from a URL")
        submitted = st.form_submit_button("Submit")
        if submitted:
            file = check_file(file_type, url)
            st.session_state[Files].append(file)
            dtypes = file.df.dtypes
            fields = pd.DataFrame(
                {
                    "name": dtypes.index,
                    "data_type": [convert_dtype(v) for v in dtypes.values],
                    "description": "",
                }
            )
            st.session_state[RecordSets].append(
                {
                    "fields": fields,
                    "name": file.name + "_record_set",
                    "description": "",
                }
            )
    for key, file in enumerate(st.session_state[Files]):
        with st.expander(f"{file.encoding_format} - {file.name}", expanded=True):

            def delete_line():
                del st.session_state[Files][key]

            name = st.text_input(
                needed_field("Name"),
                value=file.name,
            )
            description = st.text_area(
                "Description",
                placeholder="Provide a clear description of the file.",
            )
            sha256 = st.text_input(
                needed_field("SHA256"),
                value=file.sha256,
                disabled=True,
            )
            encoding_format = st.text_input(
                needed_field("Encoding format"),
                value=file.encoding_format,
                disabled=True,
            )
            st.markdown("First rows of data:")
            st.dataframe(file.df, height=DF_HEIGHT)
            _, col = st.columns([5, 1])
            col.button("Remove", key=url, on_click=delete_line, type="primary")
            file = File(
                name=name,
                description=description,
                content_url=file.content_url,
                encoding_format=encoding_format,
                sha256=sha256,
                df=file.df,
            )
            st.session_state[Files][key] = file
