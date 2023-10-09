from state import RecordSets
import streamlit as st
from views.st_utils import DF_HEIGHT

DATA_TYPES = [
    "https://schema.org/Text",
    "https://schema.org/Float",
    "https://schema.org/Integer",
    "https://schema.org/Boolean",
]


def render_record_sets():
    if not st.session_state[RecordSets]:
        st.markdown("Provide files before.")
    else:
        record_set = st.session_state[RecordSets][0]
        st.markdown("Found 1 CSV with the following types:")
        st.data_editor(
            record_set["fields"],
            height=DF_HEIGHT,
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn(
                    "name",
                    help="Name of the field",
                    required=True,
                ),
                "description": st.column_config.TextColumn(
                    "description",
                    help="Description of the field",
                    required=False,
                ),
                "data_type": st.column_config.SelectboxColumn(
                    "data_type",
                    help="The Croissant type",
                    options=DATA_TYPES,
                    required=True,
                ),
            },
        )
