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


def _data_editor_key(record_set_name: str) -> str:
    return f"{record_set_name}-dataframe"


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


def render_record_sets():
    if not st.session_state[Metadata].distribution:
        st.markdown("Please add resources first.")
        return
    record_set: RecordSet
    for key, record_set in enumerate(st.session_state[Metadata].record_sets):
        with st.expander(f"**{record_set.name}**", expanded=True):
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
            if (
                name != record_set.name
                or description != record_set.description
                or is_enumeration != record_set.is_enumeration
            ):
                record_set.name = name
                record_set.description = description
                record_set.is_enumeration = is_enumeration
                st.session_state[Metadata].update_record_set(key, record_set)
            names = [str(field.name) for field in record_set.fields]
            descriptions = [str(field.description) for field in record_set.fields]
            # TODO(https://github.com/mlcommons/croissant/issues/350): Allow to display
            # several data types, not only the first.
            data_types = [str(field.data_types[0]) for field in record_set.fields]
            fields = pd.DataFrame(
                {
                    FieldDataFrame.NAME: names,
                    FieldDataFrame.DESCRIPTION: descriptions,
                    FieldDataFrame.DATA_TYPE: data_types,
                },
                dtype=np.str_,
            )
            data_editor_key = _data_editor_key(record_set.name)
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
                },
                on_change=handle_fields_change,
                args=(key, record_set),
            )
