import csv
import hashlib
import tempfile
from typing import Any

from etils import epath
import numpy as np
import pandas as pd
import requests
import streamlit as st

import mlcroissant as mlc


class CurrentStep:
    pass


class Files:
    pass


class RecordSets:
    pass


class Metadata:
    """In the future, this could be the serialization format between front and back."""

    pass


_DF_HEIGHT = 300

# List from https://www.kaggle.com/discussions/general/116302.
licenses = [
    "Other",
    "Public Domain",
    "CC-0",
    "PDDL",
    "CC-BY",
    "CDLA-Permissive-1.0",
    "ODC-BY",
    "CC-BY-SA",
    "CDLA-Sharing-1.0",
    "ODC-ODbL",
    "CC BY-NC",
    "CC BY-ND",
    "CC BY-NC-SA",
    "CC BY-NC-ND",
]

file_types = ["text/csv"]

data_types = [
    "https://schema.org/Text",
    "https://schema.org/Float",
    "https://schema.org/Integer",
    "https://schema.org/Boolean",
]


def transform_dtype(dtype: Any):
    if dtype == np.int64:
        return "https://schema.org/Integer"
    elif dtype == np.float64:
        return "https://schema.org/Float"
    elif dtype == np.bool_:
        return "https://schema.org/Boolean"
    elif dtype == np.str_ or dtype == object:
        return "https://schema.org/Text"
    else:
        raise NotImplementedError(dtype)


if CurrentStep not in st.session_state:
    st.session_state[CurrentStep] = 1

if Files not in st.session_state:
    st.session_state[Files] = []

if Metadata not in st.session_state:
    st.session_state[Metadata] = {}

if RecordSets not in st.session_state:
    st.session_state[RecordSets] = []


def needed_field(text: str) -> str:
    return f"{text}:red[*]"


def set_form_step(action, step=None):
    """Maintains the user's location within the wizard."""
    if action == "Next":
        st.session_state[CurrentStep] = st.session_state[CurrentStep] + 1
    if action == "Back":
        st.session_state[CurrentStep] = st.session_state[CurrentStep] - 1
    if action == "Jump" and step is not None:
        st.session_state[CurrentStep] = step


def render_buttons_view():
    # Steps
    def button_type(i: int) -> str:
        """Determines button color: red when user is on that given step."""
        return "primary" if st.session_state[CurrentStep] == i else "secondary"

    st.button(
        "Metadata",
        on_click=set_form_step,
        args=["Jump", 1],
        type=button_type(1),
        use_container_width=True,
    )
    st.button(
        "Files",
        on_click=set_form_step,
        args=["Jump", 2],
        type=button_type(2),
        use_container_width=True,
    )
    st.button(
        "RecordSets",
        on_click=set_form_step,
        args=["Jump", 3],
        type=button_type(3),
        use_container_width=True,
    )


def render_wizard_view():
    with st.container():
        if st.session_state[CurrentStep] == 1:
            name = st.text_input(needed_field("Name"), placeholder="Dataset")
            description = st.text_area(
                "Description", placeholder="Provide a clear description of the dataset."
            )
            license = st.selectbox("License", options=licenses)
            url = st.text_input(needed_field("URL"), placeholder="URL to the dataset.")
            citation = st.text_area(
                "Citation",
                placeholder="@book{\n  title={Title}\n}",
            )
            if name and url:
                st.session_state[Metadata] = dict(
                    name=name,
                    description=description,
                    citation=citation,
                    license=license,
                    url=url,
                )
        elif st.session_state[CurrentStep] == 2:
            with st.form(key="manual_urls", clear_on_submit=True):
                file_type = st.selectbox("Encoding format", options=file_types)
                url = st.text_input("Import from a URL")
                submitted = st.form_submit_button("Submit")
                if submitted:

                    def check_file(encoding_format: str, url: str) -> pd.DataFrame:
                        """Downloads locally and checks the file."""
                        with requests.get(url, stream=True) as request:
                            request.raise_for_status()
                            with tempfile.TemporaryDirectory() as tmpdir:
                                tmpdir = epath.Path(tmpdir) / "file"
                                with tmpdir.open("wb") as file:
                                    for chunk in request.iter_content(chunk_size=8192):
                                        file.write(chunk)
                                with tmpdir.open("rb") as file:
                                    sha256 = hashlib.sha256(file.read()).hexdigest()
                                with tmpdir.open("rb") as file:
                                    if encoding_format == "text/csv":
                                        df = pd.read_csv(file).infer_objects()
                                        return {
                                            "name": url.split("/")[-1],
                                            "description": "",
                                            "content_url": url,
                                            "encoding_format": encoding_format,
                                            "sha256": sha256,
                                            "df": df,
                                        }
                                    else:
                                        raise NotImplementedError()

                    file = check_file(file_type, url)
                    st.session_state[Files].append(file)
                    dtypes = file["df"].dtypes
                    fields = pd.DataFrame(
                        {
                            "name": dtypes.index,
                            "data_type": [transform_dtype(v) for v in dtypes.values],
                            "description": "",
                        }
                    )
                    st.session_state[RecordSets].append(
                        {
                            "fields": fields,
                            "name": file["name"] + "_record_set",
                            "description": "",
                        }
                    )
            for key, file in enumerate(st.session_state[Files]):
                with st.expander(f"{file_type} - {file['name']}", expanded=True):

                    def delete_line():
                        del st.session_state[Files][key]

                    def on_change():
                        # TODO(marcenacp): implement the mechanism.
                        pass

                    st.text_input(
                        needed_field("Name"),
                        value=file["name"],
                        on_change=on_change,
                    )
                    st.text_area(
                        "Description",
                        placeholder="Provide a clear description of the file.",
                        on_change=on_change,
                    )
                    st.text_input(
                        needed_field("SHA256"),
                        value=file["sha256"],
                        disabled=True,
                    )
                    st.text_input(
                        needed_field("Encoding format"),
                        value=file["encoding_format"],
                        disabled=True,
                    )
                    st.markdown("First rows of data:")
                    st.dataframe(file["df"], height=_DF_HEIGHT)
                    _, col = st.columns([5, 1])
                    col.button("Remove", key=url, on_click=delete_line, type="primary")
        elif st.session_state[CurrentStep] >= 3:
            if not st.session_state[RecordSets]:
                st.markdown("Provide files before.")
            else:
                record_set = st.session_state[RecordSets][0]
                st.markdown("Found 1 CSV with the following types:")
                st.data_editor(
                    record_set["fields"],
                    height=_DF_HEIGHT,
                    use_container_width=True,
                    column_config={
                        "name": st.column_config.TextColumn(
                            "name",
                            help="Name of the field",
                            required=True,
                        ),
                        "description": st.column_config.TextColumn(
                            "description",
                            help="Description of the field",
                            required=False,
                        ),
                        "data_type": st.column_config.SelectboxColumn(
                            "data_type",
                            help="The Croissant type",
                            options=data_types,
                            required=True,
                        ),
                    },
                )

        # Footer
        footer_cols = st.columns([6, 1, 1])
        footer_cols[1].button(
            "Back",
            on_click=set_form_step,
            args=["Back"],
            disabled=st.session_state[CurrentStep] == 1,
        )
        footer_cols[2].button(
            "Next",
            on_click=set_form_step,
            args=["Next"],
            disabled=st.session_state[CurrentStep] == 4,
        )


def render_croissant_file_view():
    if not st.session_state[Metadata]:
        return st.code({}, language="json")
    try:
        distribution = []
        for file in st.session_state[Files]:
            distribution.append(
                mlc.nodes.FileObject(
                    name=file.get("name"),
                    description=file.get("description"),
                    content_url=file.get("content_url"),
                    encoding_format=file.get("encoding_format"),
                    sha256=file.get("sha256"),
                )
            )
        record_sets = []
        for record_set in st.session_state[RecordSets]:
            fields = []
            for _, field in record_set.get("fields", pd.DataFrame()).iterrows():
                fields.append(
                    mlc.nodes.Field(
                        name=field["name"],
                        description=field["description"],
                        data_types=field["data_type"],
                        source=mlc.nodes.Source(
                            uid=file.get("name"),
                            node_type="distribution",
                            extract=mlc.nodes.Extract(column=field["name"]),
                        ),
                    )
                )
            record_sets.append(
                mlc.nodes.RecordSet(
                    name=record_set["name"],
                    description=record_set["description"],
                    fields=fields,
                )
            )
        metadata = mlc.nodes.Metadata(
            name=st.session_state[Metadata].get("name"),
            citation=st.session_state[Metadata].get("citation"),
            license=st.session_state[Metadata].get("license"),
            description=st.session_state[Metadata].get("description"),
            url=st.session_state[Metadata].get("url"),
            distribution=distribution,
            record_sets=record_sets,
        )
        return st.json(metadata.to_json(), expanded=True)
    except Exception as exception:
        return st.code(exception, language="text")


st.set_page_config(page_title="Croissant Wizard", layout="wide")
st.header("Croissant Wizard")
col1, col2, col3 = st.columns([1, 3, 3], gap="medium")
with col1:
    render_buttons_view()
with col2:
    render_wizard_view()
with col3:
    render_croissant_file_view()
