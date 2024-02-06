import pandas as pd
import streamlit as st

from core.state import Metadata
import mlcroissant as mlc


def render_jsonld():
    if not st.session_state[Metadata]:
        return st.code({}, language="json")
    try:
        croissant = st.session_state[Metadata]
        distribution = []
        for file in croissant.distribution:
            distribution.append(
                mlc.FileObject(
                    name=file.name,
                    description=file.description,
                    content_url=file.content_url,
                    encoding_format=file.encoding_format,
                    sha256=file.sha256,
                )
            )
        record_sets = []
        for record_set in croissant.record_sets:
            fields = []
            for _, field in record_set.get("fields", pd.DataFrame()).iterrows():
                fields.append(
                    mlc.Field(
                        name=field["name"],
                        description=field["description"],
                        data_types=field["data_type"],
                        source=mlc.Source(
                            uid=file.name,
                            node_type="distribution",
                            extract=mlc.Extract(column=field["name"]),
                        ),
                    )
                )
            record_sets.append(
                mlc.RecordSet(
                    name=record_set["name"],
                    description=record_set["description"],
                    fields=fields,
                )
            )
        if croissant.metadata:
            metadata = mlc.Metadata(
                name=croissant.metadata.name,
                cite_as=croissant.metadata.cite_as,
                license=croissant.metadata.license,
                description=croissant.metadata.description,
                url=croissant.metadata.url,
                distribution=distribution,
                record_sets=record_sets,
            )
            return st.json(metadata.to_json(), expanded=True)
    except Exception as exception:
        return st.code(exception, language="text")
