import numpy as np
import pandas as pd
import streamlit as st

from core.state import Field
from core.state import Metadata
from core.state import RecordSet
import mlcroissant as mlc
from utils import DF_HEIGHT
from utils import needed_field

DATA_TYPES = [
    mlc.DataType.TEXT,
    mlc.DataType.FLOAT,
    mlc.DataType.INTEGER,
    mlc.DataType.BOOL,
]


class SourceType:
    DISTRIBUTION = "distribution"
    FIELD = "field"


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
    else:
        raise NotImplementedError(
            f"{source=} could not be parsed by the editor. Please contact us on GitHub"
            " by creating a new issue:"
            " https://github.com/mlcommons/croissant/issues/new"
        )


def _find_joins(fields: list[Field]) -> list[Join]:
    """Finds the existing joins in the fields."""
    joins: list[Join] = []
    for field in fields:
        if field.source and field.references:
            left = _find_left_or_right(field.source)
            right = _find_left_or_right(field.references)
            joins.append((left, right))
    return joins


def handle_fields_change(record_set_key: int, record_set: RecordSet):
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
                field.data_types = new_value
        st.session_state[Metadata].update_field(record_set_key, field_key, field)
    for added_row in result["added_rows"]:
        field = Field(
            name=added_row[FieldDataFrame.NAME],
            description=added_row[FieldDataFrame.DESCRIPTION],
            data_types=[added_row[FieldDataFrame.DATA_TYPE]],
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
    distribution = st.session_state[Metadata].distribution
    if not distribution:
        st.markdown("Please add resources first.")
        return
    record_sets = st.session_state[Metadata].record_sets
    possible_sources = _get_possible_sources(st.session_state[Metadata])
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
            data_types = [field.data_types[0] for field in record_set.fields]
            source_uids = [field.source.uid for field in record_set.fields]
            source_extracts = [
                field.source.extract.__dict__ if field.source.extract else None
                for field in record_set.fields
            ]
            source_transforms = [
                field.source.transforms.__dict__ if field.source.transforms else None
                for field in record_set.fields
            ]
            reference_uids = [
                field.references.uid if field.references else None
                for field in record_set.fields
            ]
            reference_extracts = [
                (
                    field.references.extract.__dict__
                    if field.references and field.references.extract
                    else None
                )
                for field in record_set.fields
            ]
            fields = pd.DataFrame(
                {
                    FieldDataFrame.NAME: names,
                    FieldDataFrame.DESCRIPTION: descriptions,
                    FieldDataFrame.DATA_TYPE: data_types,
                    FieldDataFrame.SOURCE_UID: source_uids,
                    FieldDataFrame.SOURCE_EXTRACT: source_extracts,
                    FieldDataFrame.SOURCE_TRANSFORM: source_transforms,
                    FieldDataFrame.REFERENCE_UID: reference_uids,
                    FieldDataFrame.REFERENCE_EXTRACT: reference_extracts,
                },
                dtype=np.str_,
            )
            data_editor_key = _data_editor_key(record_set.name)
            st.markdown(needed_field("Fields"))
            st.data_editor(
                fields,
                height=DF_HEIGHT,
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
                    FieldDataFrame.SOURCE_UID: st.column_config.SelectboxColumn(
                        FieldDataFrame.SOURCE_UID,
                        help="Source",
                        options=possible_sources,
                        required=True,
                    ),
                    FieldDataFrame.SOURCE_EXTRACT: st.column_config.TextColumn(
                        FieldDataFrame.SOURCE_EXTRACT,
                        help="The extraction methods to apply",
                        required=False,
                        disabled=True,
                    ),
                    FieldDataFrame.SOURCE_TRANSFORM: st.column_config.TextColumn(
                        FieldDataFrame.SOURCE_TRANSFORM,
                        help="The transformations to apply once it's extracted",
                        required=False,
                        disabled=True,
                    ),
                    FieldDataFrame.REFERENCE_UID: st.column_config.SelectboxColumn(
                        FieldDataFrame.REFERENCE_UID,
                        help="Reference",
                        options=possible_sources,
                        required=False,
                    ),
                    FieldDataFrame.REFERENCE_EXTRACT: st.column_config.SelectboxColumn(
                        FieldDataFrame.REFERENCE_EXTRACT,
                        help="The extraction methods to apply",
                        options=possible_sources,
                        required=False,
                        disabled=True,
                    ),
                },
                on_change=handle_fields_change,
                args=(key, record_set),
            )
