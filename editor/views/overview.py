import os

import streamlit as st

from core.state import Metadata
import mlcroissant as mlc
from utils import needed_field


def render_overview():
    metadata = st.session_state[Metadata]
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        name = st.text_input(
            label=needed_field("Name"),
            value=metadata.name,
            placeholder="Dataset",
        )
        description = st.text_area(
            label="Description",
            value=metadata.description,
            placeholder="Provide a clear description of the dataset.",
        )

        st.subheader(f"{len(metadata.distribution)} Files")
        st.subheader(f"{len(metadata.record_sets)} Record Sets")
        metadata.update_metadata(
            name=name,
            description=description,
            license=metadata.license,
            url=metadata.url,
            citation=metadata.citation,
        )
    with col2:
        if metadata.name != None and metadata.name != "":
            st.header("Croissant File Validation")
            try:
                issues = metadata.to_canonical().issues
                if issues.errors or issues.warnings:
                    st.subheader("Errors:")
                    st.text(issues.errors)
                    st.subheader("Warnings:")
                    st.text(issues.warnings)
                else:
                    st.text("No validation issues detected!")
            except mlc.ValidationError as exception:
                st.subheader("Errors:")
                st.text(exception)
