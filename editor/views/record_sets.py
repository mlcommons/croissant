import numpy as np
import pandas as pd
import streamlit as st

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
            data_types = [str(field.data_types[0]) for field in record_set.fields]
            fields = pd.DataFrame(
                {
                    FieldDataFrame.NAME: names,
                    FieldDataFrame.DESCRIPTION: descriptions,
                    FieldDataFrame.DATA_TYPE: data_types,
                },
                dtype=np.str_,
            )
            st.data_editor(
                fields,
                height=DF_HEIGHT,
                use_container_width=True,
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
            )
