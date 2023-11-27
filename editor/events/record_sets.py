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
    expand_record_set(record_set=record_set)
