from core.state import Metadata
import pandas as pd
import streamlit as st
from utils import DF_HEIGHT

DATA_TYPES = [
    "https://schema.org/Text",
    "https://schema.org/Float",
    "https://schema.org/Integer",
    "https://schema.org/Boolean",
]


def render_record_sets():
    if len(st.session_state[Metadata].record_sets) == 0:
        st.markdown("Please add files first.")
    else:
        for record_set in st.session_state[Metadata].record_sets:
            record_set_conv = pd.DataFrame(record_set.__dict__)
            with st.container():
                st.data_editor(
                    record_set_conv,
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
                    },
                )
