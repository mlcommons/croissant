import enum

import streamlit as st

from core.query_params import expand_record_set
from core.state import Metadata
from core.state import RecordSet


class RecordSetEvent(enum.Enum):
    """Event that triggers a RecordSet change."""

    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    IS_ENUMERATION = "IS_ENUMERATION"
    HAS_DATA = "HAS_DATA"
    CHANGE_DATA = "CHANGE_DATA"


def handle_record_set_change(event: RecordSetEvent, record_set: RecordSet, key: str):
    value = st.session_state[key]
    if event == RecordSetEvent.NAME:
        old_name = record_set.name
        new_name = value
        if old_name != new_name:
            metadata: Metadata = st.session_state[Metadata]
            metadata.rename_record_set(old_name=old_name, new_name=new_name)
        record_set.name = value
    elif event == RecordSetEvent.DESCRIPTION:
        record_set.description = value
    elif event == RecordSetEvent.IS_ENUMERATION:
        record_set.is_enumeration = value
    elif event == RecordSetEvent.HAS_DATA:
        if value:
            record_set.data = []
        else:
            record_set.data = None
    elif event == RecordSetEvent.CHANGE_DATA:
        for index, new_value in value["edited_rows"].items():
            record_set.data[index] = {**record_set.data[index], **new_value}
        for row in value["added_rows"]:
            record_set.data.append(row)
        for row in value["deleted_rows"]:
            del record_set.data[row]
    expand_record_set(record_set=record_set)
