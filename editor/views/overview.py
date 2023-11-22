import streamlit as st

from core.state import Metadata
import mlcroissant as mlc
from utils import needed_field
from views.metadata import handle_metadata_change
from views.metadata import MetadataEvent


def render_overview():
    metadata: Metadata = st.session_state[Metadata]
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        key = "metadata-name"
        st.text_input(
            label=needed_field("Name"),
            key=key,
            value=metadata.name,
            placeholder="Dataset",
            on_change=handle_metadata_change,
            args=(MetadataEvent.NAME, metadata, key),
        )
        key = "metadata-url"
        st.text_input(
            label=needed_field("URL"),
            key=key,
            value=metadata.url,
            placeholder="URL to the dataset.",
            on_change=handle_metadata_change,
            args=(MetadataEvent.URL, metadata, key),
        )
        key = "metadata-description"
        st.text_area(
            label="Description",
            key=key,
            value=metadata.description,
            placeholder="Provide a clear description of the dataset.",
            on_change=handle_metadata_change,
            args=(MetadataEvent.DESCRIPTION, metadata, key),
        )

        st.subheader(f"{len(metadata.distribution)} Files")
        st.subheader(f"{len(metadata.record_sets)} Record Sets")
    with col2:
        user_started_editing = metadata.record_sets or metadata.distribution
        if user_started_editing:
            st.header("Croissant File Validation")
            try:
                issues = metadata.to_canonical().issues
                if issues.errors:
                    st.subheader("Errors:")
                    for error in issues.errors:
                        st.write(error)
                if issues.warnings:
                    st.subheader("Warnings:")
                    for warning in issues.warnings:
                        st.write(warning)
                if not issues.errors and not issues.warnings:
                    st.write("No validation issues detected!")
            except mlc.ValidationError as exception:
                st.subheader("Errors:")
                st.write(str(exception))
