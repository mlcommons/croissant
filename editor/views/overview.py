import dataclasses
from typing import Any

import streamlit as st

from core.constants import NAMES_INFO
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


def _relevant_fields(class_or_instance: type):
    if isinstance(class_or_instance, type):
        return [
            field.name
            for field in dataclasses.fields(class_or_instance)
            if field.name not in _NON_RELEVANT_METADATA
        ]
    else:
        return [
            field
            for field, value in dataclasses.asdict(class_or_instance).items()
            if value and field not in _NON_RELEVANT_METADATA
        ]


def render_overview():
    metadata: Metadata = st.session_state[Metadata]
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        key = "metadata-name"
        name = st.text_input(
            label=needed_field("Name"),
            key=key,
            value=metadata.name,
            help=f"The name of the dataset. {NAMES_INFO}",
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
        col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])
        fields = len(_relevant_fields(metadata))
        metadata_weight = len(_relevant_fields(Metadata))
        completion = int(
            # Formula for the completion:
            # - Resources and RecordSets count as much as Metadata.
            # - Metadata is the percentage of filled fields.
            (
                fields
                + (metadata_weight if metadata.distribution else 0)
                + (metadata_weight if metadata.record_sets else 0)
            )
            * 100
            / (3 * metadata_weight)
        )
        col_a.metric(
            "Completion",
            f"{completion}%",
            help=(
                "Approximation of the total completion based on the number of fields"
                " that are filled."
            ),
        )
        col_b.metric("Number of metadata fields", fields)
        col_c.metric("Number of resources", len(metadata.distribution))
        col_d.metric("Number of RecordSets", len(metadata.record_sets))
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
            except mlc.ValidationError as exception:
                warning += "**Errors**\n"
                warning += f"{str(exception)}\n"
            if warning:
                st.warning(warning, icon="⚠️")
            else:
                st.success("No validation issues detected!", icon="✅")
        st.info(_INFO_TEXT, icon="💡")
