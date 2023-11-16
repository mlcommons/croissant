import numpy as np
import pandas as pd
from rdflib import term
import streamlit as st

from core.state import Field
from core.state import Metadata
from core.state import RecordSet
from core.state import SelectedRecordSet
import mlcroissant as mlc
from utils import needed_field
from views.source import ChangeEvent
from views.source import handle_field_change
from views.source import render_references
from views.source import render_source

DATA_TYPES = [
    mlc.DataType.TEXT,
    mlc.DataType.FLOAT,
    mlc.DataType.INTEGER,
    mlc.DataType.BOOL,
    mlc.DataType.URL,
]


def _handle_close_fields():
    st.session_state[SelectedRecordSet] = None


def _handle_on_click_field(
    record_set_key: int,
    record_set: RecordSet,
):
    st.session_state[SelectedRecordSet] = SelectedRecordSet(
        record_set_key=record_set_key,
        record_set=record_set,
    )


def _data_editor_key(record_set_name: str) -> str:
    return f"{record_set_name}-dataframe"


def _get_possible_sources(metadata: Metadata) -> list[str]:
    possible_sources: list[str] = []
    for resource in metadata.distribution:
        possible_sources.append(resource.name)
    for record_set in metadata.record_sets:
        for field in record_set.fields:
            possible_sources.append(f"{record_set.name}/{field.name}")
    return possible_sources


LeftOrRight = tuple[str, str]
Join = tuple[LeftOrRight, LeftOrRight]


def _find_left_or_right(source: mlc.Source) -> LeftOrRight:
    uid = source.uid
    if "/" in uid:
        parts = uid.split("/")
        return (parts[0], parts[1])
    elif source.extract.column:
        return (uid, source.extract.column)
    elif source.extract.json_path:
        return (uid, source.extract.json_path)
    elif source.extract.file_property:
        return (uid, source.extract.file_property)
    else:
        return (uid, None)


def _find_joins(fields: list[Field]) -> set[Join]:
    """Finds the existing joins in the fields."""
    joins: set[Join] = set()
    for field in fields:
        if field.source and field.references:
            left = _find_left_or_right(field.source)
            right = _find_left_or_right(field.references)
            joins.add((left, right))
    return joins


def _handle_fields_change(record_set_key: int, record_set: RecordSet):
    data_editor_key = _data_editor_key(record_set.name)
    result = st.session_state[data_editor_key]
    # `result` has the following structure:
    # {'edited_rows': {1: {}}, 'added_rows': [], 'deleted_rows': []}
    fields = record_set.fields
    for field_key in result["edited_rows"]:
        field = fields[field_key]
        new_fields = result["edited_rows"][field_key]
        for new_field, new_value in new_fields.items():
            if new_field == FieldDataFrame.NAME:
                field.name = new_value
            elif new_field == FieldDataFrame.DESCRIPTION:
                field.description = new_value
            elif new_field == FieldDataFrame.DATA_TYPE:
                field.data_types = [new_value]
        st.session_state[Metadata].update_field(record_set_key, field_key, field)
    for added_row in result["added_rows"]:
        field = Field(
            name=added_row.get(FieldDataFrame.NAME),
            description=added_row.get(FieldDataFrame.DESCRIPTION),
            data_types=[added_row.get(FieldDataFrame.DATA_TYPE)],
            source=mlc.Source(
                uid="foo",
                node_type="distribution",
                extract=mlc.Extract(column=""),
            ),
            references=mlc.Source(),
        )
        st.session_state[Metadata].add_field(record_set_key, field)
    for field_key in result["deleted_rows"]:
        st.session_state[Metadata].remove_field(record_set_key, field_key)


class FieldDataFrame:
    """Names of the columns in the pd.DataFrame for `fields`."""

    NAME = "Name"
    DESCRIPTION = "Description"
    DATA_TYPE = "Data type"
    SOURCE_UID = "Source"
    SOURCE_EXTRACT = "Source extract"
    SOURCE_TRANSFORM = "Source transform"
    REFERENCE_UID = "Reference"
    REFERENCE_EXTRACT = "Reference extract"


def render_record_sets():
    col1, col2 = st.columns([1, 1])
    with col1:
        _render_left_panel()
    with col2:
        _render_right_panel()


def _render_left_panel():
    """Left panel: visualization of all RecordSets as expandable forms."""
    distribution = st.session_state[Metadata].distribution
    if not distribution:
        st.markdown("Please add resources first.")
        return
    record_sets = st.session_state[Metadata].record_sets
    record_set: RecordSet
    for key, record_set in enumerate(record_sets):
        title = f"**{record_set.name}** ({len(record_set.fields)} fields)"
        with st.expander(title, expanded=False):
            col1, col2 = st.columns([1, 3])
            name = col1.text_input(
                needed_field("Name"),
                placeholder="Name without special character.",
                key=f"{record_set.name}-name",
                value=record_set.name,
            )
            description = col2.text_input(
                "Description",
                placeholder="Provide a clear description of the RecordSet.",
                key=f"{record_set.name}-description",
                value=record_set.description,
            )
            is_enumeration = st.checkbox(
                "Whether the RecordSet is an enumeration",
                key=f"{record_set.name}-is-enumeration",
                value=record_set.is_enumeration,
            )

            joins = _find_joins(record_set.fields)
            has_join = st.checkbox(
                "Whether the RecordSet contains joins. To add a new join, add a"
                f" field with a source in `{record_set.name}` and a reference to"
                " another RecordSet or FileSet/FileObject.",
                key=f"{record_set.name}-has-joins",
                value=bool(joins),
                disabled=True,
            )
            if has_join:
                for left, right in joins:
                    col1, col2, _, col4, col5 = st.columns([2, 2, 1, 2, 2])
                    col1.text_input(
                        "Left join",
                        disabled=True,
                        value=left[0],
                        key=f"{record_set.name}-left-join-{left}",
                    )
                    col2.text_input(
                        "Left key",
                        disabled=True,
                        value=left[1],
                        key=f"{record_set.name}-left-key-{left}",
                    )
                    col4.text_input(
                        "Right join",
                        disabled=True,
                        value=right[0],
                        key=f"{record_set.name}-right-join-{right}",
                    )
                    col5.text_input(
                        "Right key",
                        disabled=True,
                        value=right[1],
                        key=f"{record_set.name}-right-key-{right}",
                    )

            if (
                name != record_set.name
                or description != record_set.description
                or is_enumeration != record_set.is_enumeration
            ):
                record_set.name = name
                record_set.description = description
                record_set.is_enumeration = is_enumeration
                st.session_state[Metadata].update_record_set(key, record_set)
            names = [field.name for field in record_set.fields]
            descriptions = [field.description for field in record_set.fields]
            # TODO(https://github.com/mlcommons/croissant/issues/350): Allow to display
            # several data types, not only the first.
            data_types = [
                field.data_types[0] if field.data_types else None
                for field in record_set.fields
            ]
            fields = pd.DataFrame(
                {
                    FieldDataFrame.NAME: names,
                    FieldDataFrame.DESCRIPTION: descriptions,
                    FieldDataFrame.DATA_TYPE: data_types,
                },
                dtype=np.str_,
            )
            data_editor_key = _data_editor_key(record_set.name)
            st.markdown(needed_field("Fields"))
            st.data_editor(
                fields,
                use_container_width=True,
                num_rows="dynamic",
                key=data_editor_key,
                column_config={
                    FieldDataFrame.NAME: st.column_config.TextColumn(
                        FieldDataFrame.NAME,
                        help="Name of the field",
                        required=True,
                    ),
                    FieldDataFrame.DESCRIPTION: st.column_config.TextColumn(
                        FieldDataFrame.DESCRIPTION,
                        help="Description of the field",
                        required=False,
                    ),
                    FieldDataFrame.DATA_TYPE: st.column_config.SelectboxColumn(
                        FieldDataFrame.DATA_TYPE,
                        help="The Croissant type",
                        options=DATA_TYPES,
                        required=True,
                    ),
                },
                on_change=_handle_fields_change,
                args=(key, record_set),
            )

            st.button(
                "Edit fields details",
                key=f"{record_set.name}-show-fields",
                on_click=_handle_on_click_field,
                args=(key, record_set),
            )


def _render_right_panel():
    """Right panel: visualization of the clicked Field."""
    metadata: Metadata = st.session_state.get(Metadata)
    selected: SelectedRecordSet = st.session_state.get(SelectedRecordSet)
    if not selected:
        return
    record_set = selected.record_set
    record_set_key = selected.record_set_key
    with st.expander("**Fields**", expanded=True):
        for field_key, field in enumerate(record_set.fields):
            col1, col2, col3 = st.columns([1, 1, 1])

            key = f"{record_set.name}-{field.name}-name"
            col1.text_input(
                needed_field("Name"),
                placeholder="Name without special character.",
                key=key,
                value=field.name,
                on_change=handle_field_change,
                args=(ChangeEvent.NAME, record_set_key, field_key, field, key),
            )
            key = f"{record_set.name}-{field.name}-description"
            col2.text_input(
                "Description",
                placeholder="Provide a clear description of the RecordSet.",
                key=key,
                on_change=handle_field_change,
                value=field.description,
                args=(ChangeEvent.DESCRIPTION, record_set_key, field_key, field, key),
            )
            if field.data_types:
                data_type = field.data_types[0]
                if isinstance(data_type, str):
                    data_type = term.URIRef(data_type)
                if data_type in DATA_TYPES:
                    data_type_index = DATA_TYPES.index(data_type)
                else:
                    data_type_index = None
            else:
                data_type_index = None
            key = f"{record_set.name}-{field.name}-datatypes"
            col3.selectbox(
                needed_field("Data type"),
                index=data_type_index,
                options=DATA_TYPES,
                key=key,
                on_change=handle_field_change,
                args=(ChangeEvent.DATA_TYPE, record_set_key, field_key, field, key),
            )
            possible_sources = _get_possible_sources(metadata)
            render_source(
                record_set_key, record_set, field, field_key, possible_sources
            )
            render_references(
                record_set_key, record_set, field, field_key, possible_sources
            )

            st.divider()

        st.button(
            "Close",
            key=f"{record_set.name}-close-fields",
            type="primary",
            on_click=_handle_close_fields,
        )
