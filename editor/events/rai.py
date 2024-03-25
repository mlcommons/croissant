import datetime
import enum

import streamlit as st

from core.names import find_unique_name
from core.state import Metadata
import mlcroissant as mlc


class RaiEvent(enum.Enum):
    """Event that triggers a Rai change."""

    RAI_DATA_COLLECTION = "RAI_DATA_COLLECTION"
    RAI_DATA_COLLECTION_TYPE = "RAI_DATA_COLLECTION_TYPE"
    RAI_DATA_COLLECTION_TYPE_OTHERS = "RAI_DATA_COLLECTION_TYPE_OTHERS"
    RAI_DATA_COLLECTION_MISSING_DATA = "RAI_DATA_COLLECTION_MISSING_DATA"
    RAI_DATA_COLLECTION_RAW = "RAI_DATA_COLLECTION_RAW"
    RAI_DATA_COLLECTION_TIMEFRAME = "RAI_DATA_COLLECTION_TIMEFRAME"
    RAI_DATA_IMPUTATION_PROTOCOL = "RAI_DATA_IMPUTATION_PROTOCOL"
    RAI_DATA_PREPROCESSING_PROTOCOL = " RAI_DATA_PREPROCESSING_PROTOCOL"
    RAI_DATA_MANIPULATION_PROTOCOL = "RAI_DATA_MANIPULATION_PROTOCOL"
    RAI_DATA_ANNOTATION_PROTOCOL = "RAI_DATA_ANNOTATION_PROTOCOL"
    RAI_DATA_ANNOTATION_PLATFORM = "RAI_DATA_ANNOTATION_PLATFORM"
    RAI_DATA_ANNOTATION_ANALYSIS = "RAI_DATA_ANNOTATION_ANALYSIS"
    RAI_DATA_ANNOTATION_PER_ITEM = "RAI_DATA_ANNOTATION_PERI_TEM"
    RAI_DATA_ANNOTATION_DEMOGRAPHICS = "RAI_DATA_ANNOTATION_DEMOGRAPHICS"
    RAI_DATA_ANNOTATION_TOOLS = "RAI_DATA_ANNOTATION_TOOLS"
    RAI_DATA_USE_CASES = "RAI_DATA_USECASES"
    RAI_DATA_BIAS = "RAI_DATA_BIAS"
    RAI_DATA_LIMITATION = "RAI_DATA_LIMITATION"
    RAI_DATA_SOCIAL_IMPACT = "RAI_DATA_SOCIAL_IMPACT"
    RAI_SENSITIVE = "RAI_SENSITIVE"
    RAI_MAINTENANCE = "RAI_MAINTENANCE"


def handle_rai_change(event: RaiEvent, metadata: Metadata, key: str):
    ## If widget is 1-to-many we first get the index to proper update them
    index = get_widget_cadinality(key)
    if event == RaiEvent.RAI_DATA_COLLECTION:
        metadata.data_collection = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_TYPE:
        metadata.data_collection_type = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_MISSING_DATA:
        metadata.data_collection_missing_data = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_RAW:
        metadata.data_collection_raw_data = st.session_state[key]
    if event == RaiEvent.RAI_DATA_COLLECTION_TIMEFRAME:
        # To do
        pass
    if event == RaiEvent.RAI_DATA_IMPUTATION_PROTOCOL:
        metadata.data_imputation_protocol = st.session_state[key]
    if event == RaiEvent.RAI_DATA_PREPROCESSING_PROTOCOL:
        if metadata.data_preprocessing_protocol:
            metadata.data_preprocessing_protocol[int(index)] = st.session_state[key]
        else:
            metadata.data_preprocessing_protocol = []
            metadata.data_preprocessing_protocol.append(st.session_state[key])
    if event == RaiEvent.RAI_DATA_MANIPULATION_PROTOCOL:
        metadata.data_manipulation_protocol = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PROTOCOL:

        metadata.data_annotation_protocol = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PLATFORM:
        metadata.data_annotation_platform = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_ANALYSIS:
        metadata.data_annotation_analysis = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_PER_ITEM:
        metadata.annotation_per_item = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_DEMOGRAPHICS:
        metadata.annotator_demographics = st.session_state[key]
    if event == RaiEvent.RAI_DATA_ANNOTATION_TOOLS:
        metadata.machine_annotation_tools = st.session_state[key]
    if event == RaiEvent.RAI_DATA_USE_CASES:

        if metadata.data_use_cases:
            metadata.data_use_cases[int(index)] = st.session_state[key]
        else:
            metadata.data_use_cases = []
            metadata.data_use_cases.append(st.session_state[key])

    if event == RaiEvent.RAI_DATA_BIAS:

        if metadata.data_biases:
            metadata.data_biases[int(index)] = st.session_state[key]
        else:
            metadata.data_biases = []
            metadata.data_biases.append(st.session_state[key])

    if event == RaiEvent.RAI_DATA_LIMITATION:
        if metadata.data_limitations:
            metadata.data_limitations[int(index)] = st.session_state[key]
        else:
            metadata.data_limitations = []
            metadata.data_limitations.append(st.session_state[key])
    if event == RaiEvent.RAI_DATA_SOCIAL_IMPACT:
        metadata.data_social_impact = st.session_state[key]
    if event == RaiEvent.RAI_SENSITIVE:

        if metadata.personal_sensitive_information:
            metadata.personal_sensitive_information[int(index)] = st.session_state[key]
        else:
            metadata.personal_sensitive_information = []
            metadata.personal_sensitive_information.append(st.session_state[key])
    if event == RaiEvent.RAI_MAINTENANCE:
        metadata.data_release_maintenance_plan = st.session_state[key]


def get_widget_cadinality(key: str):
    return key.split("_")[-1]
