import multiprocessing
import textwrap
import time
from typing import TypedDict

import numpy as np
import pandas as pd
from rdflib import term
import streamlit as st

from core.data_types import MLC_DATA_TYPES
from core.data_types import STR_DATA_TYPES
from core.query_params import expand_record_set
from core.query_params import is_record_set_expanded
from core.state import Field
from core.state import Metadata
from core.state import RecordSet
from core.state import SelectedRecordSet
from events.record_sets import handle_record_set_change
from events.record_sets import RecordSetEvent
import mlcroissant as mlc
from utils import needed_field
from views.source import FieldEvent
from views.source import handle_field_change
from views.source import render_references
from views.source import render_source

_NUM_RECORDS = 3
_TIMEOUT_SECONDS = 1


class _Result(TypedDict):
    df: pd.DataFrame | None
    exception: Exception | None


@st.cache_data(show_spinner="Generating the dataset...")
def _generate_data_with_timeout(record_set: RecordSet) -> _Result:
    """Generates the data and waits at most _TIMEOUT_SECONDS."""
    with multiprocessing.Manager() as manager:
        result: _Result = manager.dict(df=None, exception=None)
        args = (record_set, result)
        process = multiprocessing.Process(target=_generate_data, args=args)
        process.start()
        if not process.is_alive():
            return _Result(**result)
        time.sleep(_TIMEOUT_SECONDS)
        if process.is_alive():
            process.kill()
            result["exception"] = TimeoutError(
                "The generation took too long and was killed. Please, use the CLI as"
                " described in"
                " https://github.com/mlcommons/croissant/tree/main/python/mlcroissant#verifyload-a-croissant-dataset."
            )
        return _Result(**result)


def _generate_data(record_set: RecordSet, result: _Result) -> pd.DataFrame | None:
    """Generates the first _NUM_RECORDS records."""
    try:
        metadata: Metadata = st.session_state[Metadata]
        if not metadata:
            raise ValueError(
                "The dataset is still incomplete. Please, go to the overview to see"
                " errors."
            )
        croissant = metadata.to_canonical()
        if croissant:
            dataset = mlc.Dataset.from_metadata(croissant)
            records = iter(dataset.records(record_set=record_set.name))
            df = []
            for i, record in enumerate(iter(records)):
                if i >= _NUM_RECORDS:
                    break
                # Decode bytes as str:
                for key, value in record.items():
                    if isinstance(value, bytes):
                        try:
                            record[key] = value.decode("utf-8")
                        except:
                            pass
                df.append(record)
            result["df"] = pd.DataFrame(df)
    except Exception as exception:
        result["exception"] = exception


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


def _data_editor_key(record_set_key: int, record_set: RecordSet) -> str:
    return f"{record_set_key}-{record_set.name}-dataframe"


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


def _handle_create_record_set():
    metadata: Metadata = st.session_state[Metadata]
    metadata.add_record_set(RecordSet(name="new-record-set", description=""))


def _handle_fields_change(record_set_key: int, record_set: RecordSet):
    expand_record_set(record_set=record_set)
    data_editor_key = _data_editor_key(record_set_key, record_set)
    result = st.session_state[data_editor_key]
    # `result` has the following structure:
    # ```
    # {'edited_rows': {1: {}}, 'added_rows': [], 'deleted_rows': []}
    # ```
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
    for added_row in result["added_rows"]:
        field = Field(
            name=added_row.get(FieldDataFrame.NAME),
            description=added_row.get(FieldDataFrame.DESCRIPTION),
            data_types=[added_row.get(FieldDataFrame.DATA_TYPE)],
            source=mlc.Source(),
            references=mlc.Source(),
        )
        st.session_state[Metadata].add_field(record_set_key, field)
    for field_key in result["deleted_rows"]:
        st.session_state[Metadata].remove_field(record_set_key, field_key)
    # Reset the in-line data if it exists.
    if record_set.data:
        record_set.data = []


class FieldDataFrame:
    """Names of the columns in the pd.DataFrame for `fields`."""

    NAME = "Field name"
    DESCRIPTION = "Field description"
    DATA_TYPE = "Data type"
    SOURCE_UID = "Source"
    SOURCE_EXTRACT = "Source extract"
    SOURCE_TRANSFORM = "Source transform"
    REFERENCE_UID = "Reference"
    REFERENCE_EXTRACT = "Reference extract"


def render_record_sets():
    col1, col2 = st.columns([1, 1])
    with col1:
        with st.spinner("Generating the dataset..."):
            _render_left_panel()
    with col2:
        _render_right_panel()


def _render_left_panel():
    """Left panel: visualization of all RecordSets as expandable forms."""
    record_sets = st.session_state[Metadata].record_sets
    record_set: RecordSet
    for record_set_key, record_set in enumerate(record_sets):
        title = f"**{record_set.name or '-'}** ({len(record_set.fields)} fields)"
        prefix = f"record-set-{record_set_key}"
        with st.expander(title, expanded=is_record_set_expanded(record_set)):
            col1, col2 = st.columns([1, 3])
            key = f"{prefix}-name"
            col1.text_input(
                needed_field("Name"),
                placeholder="Name without special character.",
                key=key,
                value=record_set.name,
                on_change=handle_record_set_change,
                args=(RecordSetEvent.NAME, record_set, key),
            )
            key = f"{prefix}-description"
            col2.text_input(
                "Description",
                placeholder="Provide a clear description of the RecordSet.",
                key=key,
                value=record_set.description,
                on_change=handle_record_set_change,
                args=(RecordSetEvent.DESCRIPTION, record_set, key),
            )
            key = f"{prefix}-is-enumeration"
            st.checkbox(
                "Whether the RecordSet is an enumeration",
                key=key,
                value=record_set.is_enumeration,
                on_change=handle_record_set_change,
                args=(RecordSetEvent.IS_ENUMERATION, record_set, key),
            )
            key = f"{prefix}-has-data"
            st.checkbox(
                "Whether the RecordSet has in-line data",
                key=key,
                value=bool(record_set.data),
                on_change=handle_record_set_change,
                args=(RecordSetEvent.HAS_DATA, record_set, key),
            )

            joins = _find_joins(record_set.fields)
            has_join = st.checkbox(
                "Whether the RecordSet contains joins. To add a new join, add a field"
                " with a source in `RecordSet`/`FileSet`/`FileObject` and a reference"
                " to another `RecordSet`/`FileSet`/`FileObject`.",
                key=f"{prefix}-has-joins",
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
                        key=f"{prefix}-left-join-{left[0]}-{left[1]}",
                    )
                    col2.text_input(
                        "Left key",
                        disabled=True,
                        value=left[1],
                        key=f"{prefix}-left-key-{left[0]}-{left[1]}",
                    )
                    col4.text_input(
                        "Right join",
                        disabled=True,
                        value=right[0],
                        key=f"{prefix}-right-join-{right[0]}-{right[1]}",
                    )
                    col5.text_input(
                        "Right key",
                        disabled=True,
                        value=right[1],
                        key=f"{prefix}-right-key-{right[0]}-{right[1]}",
                    )
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
            data_editor_key = _data_editor_key(record_set_key, record_set)
            st.markdown(
                f"{needed_field('Fields')} (add/delete fields by directly editing the"
                " table)"
            )
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
                        options=STR_DATA_TYPES,
                        required=True,
                    ),
                },
                on_change=_handle_fields_change,
                args=(record_set_key, record_set),
            )
            result: _Result = _generate_data_with_timeout(record_set)
            df, exception = result.get("df"), result.get("exception")
            if exception is None and df is not None and not df.empty:
                st.markdown("Previsualize the data:")
                st.dataframe(df, use_container_width=True)
            # The generation is not triggered if record_set has in-line `data`.
            elif not record_set.data:
                left, right = st.columns([1, 10])
                if exception:
                    left.button(
                        "⚠️",
                        key=f"idea-{prefix}",
                        disabled=True,
                        help=textwrap.dedent(f"""**Error**:
```
{exception}
```
"""),
                    )
                right.markdown("No preview is possible.")

            st.button(
                "Edit fields details",
                key=f"{prefix}-show-fields",
                on_click=_handle_on_click_field,
                args=(record_set_key, record_set),
            )
    st.button(
        "Create a new RecordSet",
        key=f"create-new-record-set",
        type="primary",
        on_click=_handle_create_record_set,
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
        if isinstance(record_set.data, list):
            st.markdown(
                f"{needed_field('Data')}. This RecordSet is marked as having in-line"
                " data. Please, list the data below:"
            )
            key = f"{record_set_key}-fields-data"
            columns = [field.name for field in record_set.fields]
            st.data_editor(
                pd.DataFrame(record_set.data, columns=columns),
                use_container_width=True,
                num_rows="dynamic",
                key=key,
                column_config={
                    field.name: st.column_config.TextColumn(
                        field.name,
                        help=field.description,
                        required=True,
                    )
                    for field in record_set.fields
                },
                on_change=handle_record_set_change,
                args=(RecordSetEvent.CHANGE_DATA, record_set, key),
            )
        else:
            for field_key, field in enumerate(record_set.fields):
                prefix = f"{record_set_key}-{field.name}-{field_key}"
                col1, col2, col3 = st.columns([1, 1, 1])

                key = f"{prefix}-name"
                col1.text_input(
                    needed_field("Name"),
                    placeholder="Name without special character.",
                    key=key,
                    value=field.name,
                    on_change=handle_field_change,
                    args=(FieldEvent.NAME, field, key),
                )
                key = f"{prefix}-description"
                col2.text_input(
                    "Description",
                    placeholder="Provide a clear description of the RecordSet.",
                    key=key,
                    on_change=handle_field_change,
                    value=field.description,
                    args=(FieldEvent.DESCRIPTION, field, key),
                )
                if field.data_types:
                    data_type = field.data_types[0]
                    if isinstance(data_type, str):
                        data_type = term.URIRef(data_type)
                    if data_type in MLC_DATA_TYPES:
                        data_type_index = MLC_DATA_TYPES.index(data_type)
                    else:
                        data_type_index = None
                else:
                    data_type_index = None
                key = f"{prefix}-datatypes"
                col3.selectbox(
                    needed_field("Data type"),
                    index=data_type_index,
                    options=STR_DATA_TYPES,
                    key=key,
                    on_change=handle_field_change,
                    args=(FieldEvent.DATA_TYPE, field, key),
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
            key=f"{record_set.name}-{record_set_key}-close-fields",
            type="primary",
            on_click=_handle_close_fields,
        )
