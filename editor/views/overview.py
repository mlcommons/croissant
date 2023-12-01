import dataclasses
from typing import Any

import streamlit as st

from core.state import Metadata
import mlcroissant as mlc
from utils import needed_field
from views.metadata import handle_metadata_change
from views.metadata import MetadataEvent

_NON_RELEVANT_METADATA = ["name", "distribution", "record_sets", "rdf"]

_INFO_TEXT = """Croissant files are composed of three layers:

- **Metadata** about the dataset covering Responsible AI, licensing and attributes of
                [sc\:Dataset](https://schema.org/Dataset).
- **Resources**: The contents of a dataset as the underlying files
                ([`FileObject`](https://github.com/mlcommons/croissant/blob/main/docs/croissant-spec.md#fileobject))
                and/or sets of files ([`FileSet`](https://github.com/mlcommons/croissant/blob/main/docs/croissant-spec.md#fileset)).
- **RecordSets**: the sets of structured records obtained from one or more resources
                (typically a file or set of files) and the structure of these records,
                expressed as a set of fields (e.g., the columns of a table).

The next three tabs will guide you through filling those layers. The errors if any will
be displayed on this page. Once you are ready, you can download the dataset by clicking
the export button in the upper right corner."""


def render_overview():
    metadata: Metadata = st.session_state[Metadata]
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        key = "metadata-name"
        name = st.text_input(
            label=needed_field("Name"),
            key=key,
            value=metadata.name,
            placeholder="Dataset",
            on_change=handle_metadata_change,
            args=(MetadataEvent.NAME, metadata, key),
        )
        if not name:
            st.stop()
        key = "metadata-description"
        st.text_area(
            label="Description",
            key=key,
            value=metadata.description,
            placeholder="Provide a clear description of the dataset.",
            on_change=handle_metadata_change,
            args=(MetadataEvent.DESCRIPTION, metadata, key),
        )
        st.divider()
        left, middle, right = st.columns([1, 1, 1])
        fields = [
            field
            for field, value in dataclasses.asdict(metadata).items()
            if value and field not in _NON_RELEVANT_METADATA
        ]
        left.metric("Number of metadata", len(fields))
        middle.metric("Number of resources", len(metadata.distribution))
        right.metric("Number of RecordSets", len(metadata.record_sets))
    with col2:
        user_started_editing = metadata.record_sets or metadata.distribution
        if user_started_editing:
            warning = ""
            try:
                issues = metadata.to_canonical().issues
                if issues.errors:
                    warning += "**Errors**\n"
                    for error in issues.errors:
                        warning += f"{error}\n"
                if issues.warnings:
                    warning += "**Warnings**\n"
                    for warning in issues.warnings:
                        warning += f"{warning}\n"
            except mlc.ValidationError as exception:
                warning += "**Errors**\n"
                warning += f"{str(exception)}\n"
            if warning:
                st.warning(warning, icon="⚠️")
            else:
                st.success("No validation issues detected!", icon="✅")
        st.info(_INFO_TEXT, icon="💡")
