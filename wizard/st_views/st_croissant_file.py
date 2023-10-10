import pandas as pd
from st_state import Files
from st_state import Metadata
from st_state import RecordSets
import streamlit as st

import mlcroissant as mlc


def render_croissant_file():
    if not st.session_state[Metadata] or not st.session_state[Files]:
        return st.code({}, language="json")
    try:
        distribution = []
        for file in st.session_state[Files]:
            distribution.append(
                mlc.nodes.FileObject(
                    name=file.name,
                    description=file.description,
                    content_url=file.content_url,
                    encoding_format=file.encoding_format,
                    sha256=file.sha256,
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
                            uid=file.name,
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
        if st.session_state[Metadata]:
            metadata = mlc.nodes.Metadata(
                name=st.session_state[Metadata].name,
                citation=st.session_state[Metadata].citation,
                license=st.session_state[Metadata].license,
                description=st.session_state[Metadata].description,
                url=st.session_state[Metadata].url,
                distribution=distribution,
                record_sets=record_sets,
            )
            return st.json(metadata.to_json(), expanded=True)
    except Exception as exception:
        return st.code(exception, language="text")
